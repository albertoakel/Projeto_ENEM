"""Leitura otimizada de Parquet para o Dashboard ENEM.

Implementação de produção baseada nos testes de otimização de memória
realizados para a UF PA:
- Memory Pool configurado pelo processo de inicialização (system);
- use_threads=False;
- read_dictionary=True para colunas textuais selecionadas;
- Parquets separados por referência e Row Groups de 100 mil linhas;
- downcasting numérico aprovado na tolerância do diagnóstico.

Para UFs sem variante separada, utiliza os Parquets convencionais e mantém
os filtros de referência do loader original.
"""

import logging
import os
import time
import unicodedata
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import pandas as pd
import psutil
import pyarrow as pa
import pyarrow.parquet as pq

from .config import CONSUMO_DIR, DATA_DIR, PROJECT_ROOT

_LOG = logging.getLogger("enem.dados.otimizado")
_PROCESSO = psutil.Process()

# Configuração selecionada no Diagnóstico 08.
USE_THREADS = False
READ_DICTIONARY = True
APPLY_DOWNCAST = os.environ.get("ENEM_APPLY_DOWNCAST", "1") == "1"
LAYOUT_OTIMIZADO = "separado_rg_100000"
UF_VARIANTES = {"PA"}

POOL_BACKEND_SOLICITADO = os.environ.get("ARROW_DEFAULT_MEMORY_POOL", "system")
POOL_BACKEND_REAL = pa.default_memory_pool().backend_name
POOL_BACKEND_CONFIRMADO = POOL_BACKEND_SOLICITADO == POOL_BACKEND_REAL

# O diretório pode ser sobrescrito sem editar o código.
VARIANT_DIR = Path(
    os.environ.get(
        "ENEM_PARQUET_VARIANT_DIR",
        str(PROJECT_ROOT / "data" / "consumo_otimizado" / "parquet_variants"),
    )
).expanduser().resolve()

if not POOL_BACKEND_CONFIRMADO:
    _LOG.warning(
        "Memory Pool divergente: solicitado=%s | real=%s. "
        "Confira ARROW_DEFAULT_MEMORY_POOL antes de iniciar o processo.",
        POOL_BACKEND_SOLICITADO,
        POOL_BACKEND_REAL,
    )
else:
    _LOG.info("Memory Pool Arrow confirmado: %s", POOL_BACKEND_REAL)

# Mesma lista de candidatas utilizada no Notebook 08. A seleção efetiva é
# conferida contra o schema de cada arquivo, para ignorar colunas não textuais.
CANDIDATAS_DICIONARIO = {
    "painel": ["TIPO_REFERENCIA_TERRITORIAL"],
    "faixa": ["TIPO_REFERENCIA_TERRITORIAL"],
    "grupo": ["TIPO_REFERENCIA_TERRITORIAL", "tipo_grupo", "grupo", "disciplina"],
    "dsp": ["TIPO_REFERENCIA_TERRITORIAL", "sexo", "faixa_etaria", "disciplina"],
}

COLUNAS = {
    "painel": [
        "ano", "CO_MUNICIPIO_TERRITORIO", "TIPO_REFERENCIA_TERRITORIAL",
        "n_participantes", "n_masculino", "n_feminino",
        "n_faixa_etaria_informada", "n_escola_federal",
        "n_escola_estadual", "n_escola_municipal", "n_escola_privada",
        "n_escola_nao_informada", "media_redacao", "n_validos_redacao",
        "media_objetiva", "n_validos_objetiva", "media_cn", "n_validos_cn",
        "media_ch", "n_validos_ch", "media_lc", "n_validos_lc",
        "media_mt", "n_validos_mt",
    ],
    "faixa": [
        "ano", "CO_MUNICIPIO_TERRITORIO", "TIPO_REFERENCIA_TERRITORIAL",
        "TP_FAIXA_ETARIA", "n_participantes",
    ],
    "grupo": [
        "ano", "CO_MUNICIPIO_TERRITORIO", "TIPO_REFERENCIA_TERRITORIAL",
        "tipo_grupo", "grupo", "disciplina", "media", "n_validos",
        "mediana", "std", "q1", "q3",
    ],
    "dsp": [
        "ano", "CO_MUNICIPIO_TERRITORIO", "TIPO_REFERENCIA_TERRITORIAL",
        "sexo", "faixa_etaria", "disciplina", "n_participantes",
        "n_validos", "media", "std",
    ],
}

NOMES_ARQUIVOS = {
    "painel": "painel_municipal.parquet",
    "faixa": "faixa_etaria_municipal.parquet",
    "grupo": "desempenho_grupos_municipal.parquet",
    "dsp": "desempenho_sexo_faixa_etaria_municipal.parquet",
}


def _memoria_processo():
    memoria = _PROCESSO.memory_full_info()
    return memoria.rss / 1024**2, memoria.uss / 1024**2


@contextmanager
def _tempo(nome):
    rss_ini, uss_ini = _memoria_processo()
    inicio = time.perf_counter()
    _LOG.info(
        "MEMÓRIA INÍCIO | %-36s | RSS=%.1f MB | USS=%.1f MB",
        nome, rss_ini, uss_ini,
    )
    try:
        yield
    finally:
        rss_fim, uss_fim = _memoria_processo()
        _LOG.info(
            "MEMÓRIA FIM | %-36s | RSS=%.1f MB | USS=%.1f MB "
            "| variação USS=%+.1f MB | tempo=%.3f s",
            nome, rss_fim, uss_fim, uss_fim - uss_ini,
            time.perf_counter() - inicio,
        )


def normalizar_nome(nome):
    if not isinstance(nome, str):
        return nome
    return (
        unicodedata.normalize("NFKD", nome)
        .encode("ascii", "ignore")
        .decode("ascii")
        .upper()
        .strip()
    )


def _criar_mapa_nomes(df_shape):
    base = df_shape[["CD_MUN", "NM_MUN"]]
    codigos = base["CD_MUN"].astype(str)
    nomes = base["NM_MUN"].map(normalizar_nome)
    mapa = pd.DataFrame({"CD_MUN": codigos, "NM_MUN": nomes})
    return (
        mapa.drop_duplicates(subset=["CD_MUN"])
        .set_index("CD_MUN")["NM_MUN"]
        .to_dict()
    )


def _aplicar_mapa_nomes(df, mapa_nomes):
    df["NO_MUNICIPIO_TERRITORIO"] = (
        df["CO_MUNICIPIO_TERRITORIO"].astype(str).map(mapa_nomes)
    )
    return df


def update_nomes(df, df_shape):
    # Mantém a função pública sem alterar o DataFrame recebido.
    return _aplicar_mapa_nomes(df.copy(), _criar_mapa_nomes(df_shape))


@lru_cache(maxsize=128)
def _colunas_dictionary(caminho_str, base):
    caminho = Path(caminho_str)
    schema = pq.read_schema(caminho)
    saida = []
    for coluna in CANDIDATAS_DICIONARIO[base]:
        if coluna not in schema.names:
            continue
        tipo = str(schema.field(coluna).type)
        if tipo in ("string", "large_string", "binary", "large_binary"):
            saida.append(coluna)
    return tuple(saida)


def _caminho_entrada(uf, referencia, base):
    """Retorna (caminho, layout, aplicar_filtro)."""
    if uf in UF_VARIANTES and referencia in ("ESC", "PROVA"):
        caminho = (
            VARIANT_DIR / base / LAYOUT_OTIMIZADO / f"{referencia}.parquet"
        )
        if not caminho.is_file():
            raise FileNotFoundError(
                f"Variante otimizada ausente: {caminho}\n"
                "Copie os Parquets de produção para data/consumo_otimizado ou configure "
                "ENEM_PARQUET_VARIANT_DIR para a pasta parquet_variants correta."
            )
        return caminho, LAYOUT_OTIMIZADO, False

    caminho = Path(CONSUMO_DIR) / f"uf={uf}" / NOMES_ARQUIVOS[base]
    if not caminho.is_file():
        raise FileNotFoundError(f"Parquet original ausente: {caminho}")
    return caminho, "original", referencia in ("ESC", "PROVA")


def _preparar_tabela(df, mapa_nomes, referencia=None):
    # Mantém a harmonização do loader original.
    df["TIPO_REFERENCIA_TERRITORIAL"] = (
        df["TIPO_REFERENCIA_TERRITORIAL"].replace("RESIDENCIA", "ESC")
    )
    if referencia in ("ESC", "PROVA"):
        df = df.loc[df["TIPO_REFERENCIA_TERRITORIAL"].eq(referencia)]
    _aplicar_mapa_nomes(df, mapa_nomes)
    return df.dropna(subset=["NO_MUNICIPIO_TERRITORIO"]).reset_index(drop=True)


def _aplicar_downcast(df):
    """Aplica exatamente a regra aprovada no Diagnóstico 08."""
    for coluna in df.columns:
        serie = df[coluna]
        dtype_original = str(serie.dtype)
        if pd.api.types.is_integer_dtype(serie.dtype) and dtype_original in ("int64", "uint64"):
            df[coluna] = pd.to_numeric(serie, downcast="integer")
        elif pd.api.types.is_float_dtype(serie.dtype) and dtype_original == "float64":
            df[coluna] = serie.astype("float32")
    return df


def _ler_parquet(caminho, base, referencia, aplicar_filtro):
    valores_referencia = None
    filtros = None
    if aplicar_filtro and referencia == "ESC":
        valores_referencia = ["ESC", "RESIDENCIA"]
    elif aplicar_filtro and referencia == "PROVA":
        valores_referencia = ["PROVA"]

    if valores_referencia is not None:
        filtros = [("TIPO_REFERENCIA_TERRITORIAL", "in", valores_referencia)]

    kwargs = {
        "engine": "pyarrow",
        "columns": COLUNAS[base],
        "use_threads": USE_THREADS,
        "filters": filtros,
    }
    if READ_DICTIONARY:
        selecionadas = _colunas_dictionary(str(caminho), base)
        if selecionadas:
            kwargs["read_dictionary"] = list(selecionadas)

    return pd.read_parquet(caminho, **kwargs)


def read_allfiles2(UF, P=None):
    uf = str(UF).strip().upper()
    referencia = P.strip().upper() if isinstance(P, str) else None
    if referencia not in ("ESC", "PROVA"):
        referencia = None

    arquivo_shape = (
        Path(DATA_DIR) / "shapefiles" / f"{uf}_Municipios_2025" /
        f"{uf}_Municipios_2025.shp"
    )
    if not arquivo_shape.is_file():
        raise FileNotFoundError(f"Shapefile ausente para UF={uf}: {arquivo_shape}")

    caminhos = {}
    layouts = {}
    filtros = {}
    for base in ("painel", "faixa", "grupo", "dsp"):
        caminhos[base], layouts[base], filtros[base] = _caminho_entrada(
            uf, referencia, base
        )

    _LOG.info(
        "LEITURA OTIMIZADA | UF=%s | referência=%s | pool=%s | threads=%s "
        "| dictionary=%s | downcast=%s | layout=%s",
        uf, referencia or "ESC+PROVA", POOL_BACKEND_REAL,
        USE_THREADS, READ_DICTIONARY, APPLY_DOWNCAST,
        sorted(set(layouts.values())),
    )

    tabelas = {}
    for base in ("painel", "faixa", "grupo", "dsp"):
        with _tempo(f"parquet {base} ({layouts[base]})"):
            tabelas[base] = _ler_parquet(
                caminhos[base], base, referencia, filtros[base]
            )

    with _tempo(f"shapefile {uf}"):
        shape = gpd.read_file(arquivo_shape)

    with _tempo("criar mapa de nomes municipais"):
        mapa_nomes = _criar_mapa_nomes(shape)

    for base in ("painel", "faixa", "grupo", "dsp"):
        with _tempo(f"preparar tabela {base}"):
            tabelas[base] = _preparar_tabela(
                tabelas[base], mapa_nomes, referencia
            )
            if APPLY_DOWNCAST:
                tabelas[base] = _aplicar_downcast(tabelas[base])

    _LOG.info(
        "LINHAS APÓS PROCESSAMENTO | painel=%s faixa=%s grupo=%s dsp=%s "
        "| municípios=%s",
        len(tabelas["painel"]), len(tabelas["faixa"]),
        len(tabelas["grupo"]), len(tabelas["dsp"]), len(shape),
    )

    ref_saida = referencia if referencia else "ESC & PROVA"
    return {
        "painel": {"caminho": caminhos["painel"], "data": tabelas["painel"]},
        "faixa": {"caminho": caminhos["faixa"], "data": tabelas["faixa"]},
        "grupo": {"caminho": caminhos["grupo"], "data": tabelas["grupo"]},
        "dsp": {"caminho": caminhos["dsp"], "data": tabelas["dsp"]},
        "shape": {"caminho": arquivo_shape, "data": shape},
        "ref": ref_saida,
    }


def codigo_como_texto(serie):
    return serie.astype("string").str.replace(r"\.0$", "", regex=True).str.strip()


def status_loader_otimizado():
    return {
        "memory_pool_solicitado": POOL_BACKEND_SOLICITADO,
        "memory_pool_real": POOL_BACKEND_REAL,
        "memory_pool_confirmado": POOL_BACKEND_CONFIRMADO,
        "use_threads": USE_THREADS,
        "read_dictionary": READ_DICTIONARY,
        "apply_downcast": APPLY_DOWNCAST,
        "layout": LAYOUT_OTIMIZADO,
        "variant_dir": str(VARIANT_DIR),
    }
