#features_names.py
from pathlib import Path
import sys

diretorio_atual = Path.cwd().resolve()

if diretorio_atual.name in {"utils"}:
    raiz_projeto = diretorio_atual.parent
else:
    raiz_projeto = diretorio_atual

src_dir = raiz_projeto

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))



import logging
import time
import unicodedata
from contextlib import contextmanager

import pandas as pd
import geopandas as gpd

_LOG = logging.getLogger("enem.dados")


@contextmanager
def _tempo(nome):
    ini = time.perf_counter()
    try:
        yield
    finally:
        _LOG.info("    · %-42s %8.2f s", nome, time.perf_counter() - ini)

# ==============================================================================
# MÓDULO DE HARMONIZAÇÃO E NORMALIZAÇÃO TERRITORIAL E LEITURA
# ==============================================================================
# Funções auxiliares para a padronização de nomes e a
# atualização de rótulos municipais em DataFrames analíticos com base nos
# geocódigos oficiais e na malha territorial (shapefile).
# ==============================================================================
def normalizar_nome(nome):
    """Normaliza strings de nomes de municípios para padronização de
        comparação.
        """
    if not isinstance(nome, str):
        return nome
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")

    return nome.upper().strip()


def update_nomes(df, df_shape):
    """Atualiza e harmoniza os nomes dos municípios no DataFrame de destino com
            base nos nomes oficiais contidos na malha geográfica (shapefile).

            O cruzamento é realizado de forma exata utilizando o geocódigo do município
            (CD_MUN -> CO_MUNICIPIO_TERRITORIO) como chave primária, garantindo a
            correção de divergências ortográficas ou de grafia
            """
    df = df.copy()
    shape = df_shape.copy()
    shape["CD_MUN"] = shape["CD_MUN"].astype(str)
    shape["NM_MUN"] = shape["NM_MUN"].apply(normalizar_nome)

    mapa_nomes = (shape.drop_duplicates(subset=["CD_MUN"])
                  .set_index("CD_MUN")["NM_MUN"].to_dict())

    df["NO_MUNICIPIO_TERRITORIO"] = (
        df["CO_MUNICIPIO_TERRITORIO"].astype(str).map(mapa_nomes)
    )
    return df


def read_allfiles(UF):
    from enem_pipeline.config import CONSUMO_DIR,DATA_DIR

    # ============================================================
    # ARQUIVOS
    # ============================================================
#
    CONSUMO_UF_DIR = CONSUMO_DIR / f"uf={UF}"

    ARQUIVO_PAINEL = CONSUMO_UF_DIR / "painel_municipal.parquet"
    ARQUIVO_FAIXA = CONSUMO_UF_DIR / "faixa_etaria_municipal.parquet"
    ARQUIVO_GRUPO = CONSUMO_UF_DIR / "desempenho_grupos_municipal.parquet"
    ARQUIVO_SHAPE = (DATA_DIR / "shapefiles" / f"{UF}_Municipios_2025" / f"{UF}_Municipios_2025.shp")



    painel = pd.read_parquet(ARQUIVO_PAINEL)
    faixa = pd.read_parquet(ARQUIVO_FAIXA)
    grupo = pd.read_parquet(ARQUIVO_GRUPO)
    shape = gpd.read_file(ARQUIVO_SHAPE)

    painel = update_nomes(painel, shape.copy())
    faixa = update_nomes(faixa, shape.copy())
    grupo = update_nomes(grupo, shape.copy())

    OUT = {
        "painel": {
            "caminho":  ARQUIVO_PAINEL,
            "data": painel},
        "faixa": {
            "caminho":  ARQUIVO_FAIXA,
            "data":  faixa},
        "grupo": {
            "caminho":  ARQUIVO_GRUPO,
            "data":  grupo,
        },
        "shape": {
            "caminho":  ARQUIVO_SHAPE,
            "data": shape,
        },
    }

    return OUT


def read_allfiles2(UF, P=None):
    out={}
    from enem_pipeline.config import CONSUMO_DIR, DATA_DIR

    # ============================================================
    # ARQUIVOS
    # ============================================================
    #
    CONSUMO_UF_DIR = CONSUMO_DIR / f"uf={UF}"

    ARQUIVO_PAINEL = CONSUMO_UF_DIR / "painel_municipal.parquet"
    ARQUIVO_FAIXA = CONSUMO_UF_DIR / "faixa_etaria_municipal.parquet"
    ARQUIVO_GRUPO = CONSUMO_UF_DIR / "desempenho_grupos_municipal.parquet"
    ARQUIVO_DSP = CONSUMO_UF_DIR / "desempenho_sexo_faixa_etaria_municipal.parquet"

    ARQUIVO_SHAPE = (DATA_DIR / "shapefiles" / f"{UF}_Municipios_2025" / f"{UF}_Municipios_2025.shp")


    _LOG.info("  Lendo arquivos de %s (referência=%s)", UF, P)
    with _tempo("parquet painel"):
        painel = pd.read_parquet(ARQUIVO_PAINEL)
    with _tempo("parquet faixa etária"):
        faixa = pd.read_parquet(ARQUIVO_FAIXA)
    with _tempo("parquet desempenho por grupo"):
        grupo = pd.read_parquet(ARQUIVO_GRUPO)
    with _tempo("parquet desempenho sexo x faixa"):
        dsp = pd.read_parquet(ARQUIVO_DSP)

    with _tempo(f"shapefile {UF} (geopandas)"):
        shape = gpd.read_file(ARQUIVO_SHAPE)
    _LOG.info("    linhas: painel=%s faixa=%s grupo=%s dsp=%s | municípios no shape=%s",
              len(painel), len(faixa), len(grupo), len(dsp), len(shape))

    # 1) update nomes
    with _tempo("harmonizar nomes municipais (x4)"):
        painel = update_nomes(painel, shape)
        faixa  = update_nomes(faixa, shape)
        grupo  = update_nomes(grupo, shape)
        dsp    = update_nomes(dsp, shape)


    # 2) RESIDENCIAl -> ESC
    painel['TIPO_REFERENCIA_TERRITORIAL'] = painel['TIPO_REFERENCIA_TERRITORIAL'].replace('RESIDENCIA', 'ESC')
    faixa['TIPO_REFERENCIA_TERRITORIAL']  = faixa['TIPO_REFERENCIA_TERRITORIAL'].replace('RESIDENCIA', 'ESC')
    grupo['TIPO_REFERENCIA_TERRITORIAL']  = grupo['TIPO_REFERENCIA_TERRITORIAL'].replace('RESIDENCIA', 'ESC')
    dsp['TIPO_REFERENCIA_TERRITORIAL']    = dsp['TIPO_REFERENCIA_TERRITORIAL'].replace('RESIDENCIA', 'ESC')


    # 3) filtragem relativo a origem
    # Quem estoudou fora do estado é descartado
    painel = painel.dropna(subset=['NO_MUNICIPIO_TERRITORIO']).copy().reset_index(drop=True)
    faixa  = faixa.dropna(subset=['NO_MUNICIPIO_TERRITORIO']).copy().reset_index(drop=True)
    grupo  = grupo.dropna(subset=['NO_MUNICIPIO_TERRITORIO']).copy().reset_index(drop=True)
    dsp    = dsp.dropna(subset=['NO_MUNICIPIO_TERRITORIO']).copy().reset_index(drop=True)


    # 4) Selecao do grupo TERRITORAL
    if P is None or P.upper() not in ('ESC', 'PROVA'):
        OUT = {"painel": {"caminho": ARQUIVO_PAINEL,
                          "data": painel},
               "faixa": {"caminho": ARQUIVO_FAIXA,
                         "data": faixa},
               "grupo": {"caminho": ARQUIVO_GRUPO,
                         "data": grupo},
               "dsp": {"caminho": ARQUIVO_DSP,
                         "data": dsp},
               "shape": {"caminho": ARQUIVO_SHAPE,
                         "data": shape},
               "ref": 'ESC & PROVA'}
        return OUT
    opcao = P.upper()
    if opcao == 'ESC':
        #print("REMOVER REFERENCIA_TERRITORIAL PROVA")
        painel = painel.drop(painel[painel['TIPO_REFERENCIA_TERRITORIAL'] == 'PROVA'].index).reset_index(drop=True)
        faixa = faixa.drop(faixa[faixa['TIPO_REFERENCIA_TERRITORIAL'] == 'PROVA'].index).reset_index(drop=True)
        grupo = grupo.drop(grupo[grupo['TIPO_REFERENCIA_TERRITORIAL'] == 'PROVA'].index).reset_index(drop=True)
        dsp = dsp.drop(dsp[dsp['TIPO_REFERENCIA_TERRITORIAL'] == 'PROVA'].index).reset_index(drop=True)

    else:
        #print("REMOVER REFERENCIA_TERRITORIAL ESC")
        painel = painel.drop(painel[painel['TIPO_REFERENCIA_TERRITORIAL'] == 'ESC'].index).reset_index(drop=True)
        faixa = faixa.drop(faixa[faixa['TIPO_REFERENCIA_TERRITORIAL'] == 'ESC'].index).reset_index(drop=True)
        grupo = grupo.drop(grupo[grupo['TIPO_REFERENCIA_TERRITORIAL'] == 'ESC'].index).reset_index(drop=True)
        dsp = dsp.drop(dsp[dsp['TIPO_REFERENCIA_TERRITORIAL'] == 'ESC'].index).reset_index(drop=True)


    # 5) ORGANIZAR SAIDA
    OUT = {
            "painel": {
                "caminho": ARQUIVO_PAINEL,
                "data": painel},
            "faixa": {
                "caminho": ARQUIVO_FAIXA,
                "data": faixa},
            "grupo": {
                "caminho": ARQUIVO_GRUPO,
                "data": grupo},
            "dsp": {"caminho": ARQUIVO_DSP,
                         "data": dsp},
            "shape": {
                "caminho": ARQUIVO_SHAPE,
                "data": shape},
            "ref": opcao}

    return OUT


# # Chave auxiliar para junções: não altera os nomes municipais.
def codigo_como_texto(serie):
    return (
        serie.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )
if __name__ == "__main__":
    UF='PA'
    read_allfiles(UF)
