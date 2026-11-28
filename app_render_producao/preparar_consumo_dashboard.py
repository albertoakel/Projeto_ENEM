#!/usr/bin/env python3
"""Prepara os Parquets de uma UF para o Dashboard ENEM.

Uso:
    python preparar_consumo_dashboard.py --uf PA
    python preparar_consumo_dashboard.py --uf PA --dry-run
    python preparar_consumo_dashboard.py --uf PA --force

Os quatro Parquets originais são preservados. A saída fica em:
    data/consumo/uf=PA/otimizado/
        painel_ESC.parquet       painel_PROVA.parquet
        faixa_ESC.parquet        faixa_PROVA.parquet
        grupo_ESC.parquet        grupo_PROVA.parquet
        dsp_ESC.parquet          dsp_PROVA.parquet
        manifest.json

A preparação reproduz o formato aprovado nos diagnósticos: projeção das
colunas do dashboard, RESIDENCIA -> ESC, separação ESC/PROVA, Row Groups de
100.000 linhas, compressão Snappy e dictionary encoding. Não aplica downcast;
o downcast continua sendo responsabilidade do loader durante a leitura.
"""

from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# O backend do Memory Pool precisa ser selecionado antes da importação do PyArrow.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from dash_utils.features_names import COLUNAS, LAYOUT_OTIMIZADO, NOMES_ARQUIVOS
from dash_utils.ufs import UFS


LOG = logging.getLogger("preparar_consumo_dashboard")
VERSAO_PREPARADOR = "1.1.0"
ROW_GROUP_SIZE = 100_000
REFERENCIAS = ("ESC", "PROVA")
BASES = tuple(NOMES_ARQUIVOS)
NOME_MANIFESTO = "manifest.json"


def configurar_log() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def normalizar_uf(valor: str) -> str:
    uf = str(valor).strip().upper()
    if uf not in UFS:
        raise ValueError(f"UF inválida: {valor!r}. Informe uma das 27 siglas oficiais.")
    return uf


def assinatura_dataframe(df: pd.DataFrame) -> dict[str, int]:
    """Assinatura de conteúdo independente do índice do DataFrame."""
    hashes = pd.util.hash_pandas_object(df, index=False).to_numpy(dtype=np.uint64)
    return {
        "linhas": int(len(df)),
        "hash_soma_uint64": int(hashes.sum(dtype=np.uint64)),
        "hash_xor_uint64": int(np.bitwise_xor.reduce(hashes, initial=np.uint64(0))),
    }


def tamanho_mb(caminho: Path) -> float:
    return caminho.stat().st_size / (1024**2)


def arquivos_originais(source_dir: Path) -> dict[str, Path]:
    return {base: source_dir / nome for base, nome in NOMES_ARQUIVOS.items()}


def caminhos_saida(source_dir: Path) -> dict[tuple[str, str], Path]:
    destino_base = source_dir / LAYOUT_OTIMIZADO
    return {
        (base, referencia): destino_base / f"{base}_{referencia}.parquet"
        for base in BASES
        for referencia in REFERENCIAS
    }


def validar_originais(source_dir: Path) -> tuple[dict[str, Path] | None, int]:
    """Valida existência dos quatro arquivos originais da UF."""
    if not source_dir.is_dir():
        LOG.error(
            "Os dados originais da UF ainda não foram disponibilizados/processados. "
            "Diretório esperado: %s",
            source_dir,
        )
        return None, 2

    originais = arquivos_originais(source_dir)
    ausentes = [caminho for caminho in originais.values() if not caminho.is_file()]
    if ausentes:
        LOG.error("Os dados originais da UF estão incompletos. Arquivos ausentes:")
        for caminho in ausentes:
            LOG.error("  - %s", caminho.name)
        return None, 2

    return originais, 0


def estado_saida(source_dir: Path, uf: str) -> tuple[bool, list[Path], Path]:
    saidas = caminhos_saida(source_dir)
    existentes = [
        caminho for caminho in saidas.values()
        if caminho.is_file() and caminho.stat().st_size > 0
    ]
    destino_layout = source_dir / LAYOUT_OTIMIZADO
    manifesto = destino_layout / NOME_MANIFESTO

    manifesto_valido = False
    if manifesto.is_file():
        try:
            dados = json.loads(manifesto.read_text(encoding="utf-8"))
            manifesto_valido = (
                dados.get("uf") == uf
                and dados.get("validacao_geral", {}).get("todos_validos", False)
                and dados.get("validacao_geral", {}).get("quantidade_arquivos") == 8
            )
        except (OSError, json.JSONDecodeError):
            manifesto_valido = False

    completo = len(existentes) == len(saidas) and manifesto_valido
    return completo, existentes, manifesto


def validar_entrada(caminho: Path, colunas: list[str], base: str) -> None:
    schema = pq.read_schema(caminho)
    ausentes = [coluna for coluna in colunas if coluna not in schema.names]
    if ausentes:
        raise ValueError(
            f"A base {base} não contém as colunas esperadas: {ausentes}. "
            f"Arquivo: {caminho}"
        )


def transformar_base(
    base: str,
    origem: Path,
    staging_layout: Path,
) -> list[dict[str, Any]]:
    colunas = COLUNAS[base]
    validar_entrada(origem, colunas, base)

    LOG.info("Lendo base %s: %s", base, origem.name)
    df = pd.read_parquet(
        origem,
        engine="pyarrow",
        columns=colunas,
        use_threads=False,
    )

    coluna_referencia = "TIPO_REFERENCIA_TERRITORIAL"
    if coluna_referencia not in df.columns:
        raise ValueError(f"Coluna {coluna_referencia!r} ausente na base {base}.")

    # A equivalência esperada é calculada após a mesma normalização validada
    # nos diagnósticos de geração das variantes.
    df[coluna_referencia] = df[coluna_referencia].replace("RESIDENCIA", "ESC")

    if df[coluna_referencia].isna().any():
        quantidade = int(df[coluna_referencia].isna().sum())
        raise ValueError(
            f"A base {base} contém {quantidade} registros sem referência territorial. "
            "A preparação foi interrompida para evitar descarte silencioso."
        )

    valores = set(df[coluna_referencia].unique().tolist())
    inesperados = sorted(str(valor) for valor in valores if valor not in REFERENCIAS)
    if inesperados:
        raise ValueError(
            f"A base {base} contém referências territoriais inesperadas: {inesperados}. "
            "Nenhum registro será descartado automaticamente."
        )

    resultados: list[dict[str, Any]] = []
    for referencia in REFERENCIAS:
        parte = df.loc[df[coluna_referencia].eq(referencia), colunas].copy()
        if parte.empty:
            raise ValueError(
                f"A base {base} não possui registros para {referencia}; "
                "não será gerado um Parquet vazio."
            )

        esperado = assinatura_dataframe(parte)
        destino = staging_layout / f"{base}_{referencia}.parquet"
        destino.parent.mkdir(parents=True, exist_ok=True)

        tabela = pa.Table.from_pandas(parte, preserve_index=False)
        pq.write_table(
            tabela,
            destino,
            row_group_size=ROW_GROUP_SIZE,
            compression="snappy",
            use_dictionary=True,
        )

        parquet_file = pq.ParquetFile(destino)
        metadata = parquet_file.metadata
        if metadata.num_rows != len(parte):
            raise AssertionError(
                f"Contagem de linhas divergente em {destino}: "
                f"esperado={len(parte)}, gravado={metadata.num_rows}."
            )

        del tabela, parte
        gc.collect()

        lido = pd.read_parquet(destino, engine="pyarrow")
        if list(lido.columns) != colunas:
            raise AssertionError(
                f"Ordem das colunas divergente em {destino}. "
                f"Esperado={colunas}; obtido={list(lido.columns)}"
            )
        obtido = assinatura_dataframe(lido)
        if obtido != esperado:
            raise AssertionError(
                f"Validação de conteúdo falhou em {base}/{referencia}. "
                f"Esperado={esperado}; obtido={obtido}"
            )

        registro = {
            "base": base,
            "referencia": referencia,
            "arquivo": str(Path(LAYOUT_OTIMIZADO) / destino.name),
            "linhas": metadata.num_rows,
            "colunas": len(colunas),
            "row_groups": metadata.num_row_groups,
            "tamanho_mb": round(tamanho_mb(destino), 3),
            "hash_soma_uint64": obtido["hash_soma_uint64"],
            "hash_xor_uint64": obtido["hash_xor_uint64"],
            "validacao": "OK",
        }
        resultados.append(registro)
        LOG.info(
            "VALIDADO | %-6s | %-5s | %s linhas | %s row groups | %.2f MB",
            base,
            referencia,
            f"{metadata.num_rows:,}",
            metadata.num_row_groups,
            tamanho_mb(destino),
        )
        del lido
        gc.collect()

    del df
    gc.collect()
    return resultados


def informacoes_origem(originais: dict[str, Path]) -> dict[str, dict[str, Any]]:
    saida = {}
    for base, caminho in originais.items():
        stat = caminho.stat()
        saida[base] = {
            "arquivo": caminho.name,
            "tamanho_bytes": stat.st_size,
            "modificado_em_utc": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(),
        }
    return saida


def promover_resultados(staging_layout: Path, destino_layout: Path, source_dir: Path) -> None:
    """Substitui a pasta otimizada inteira, preservando-a em caso de falha."""
    temporarios = sorted(staging_layout.glob("*_*.parquet"))
    esperado = len(BASES) * len(REFERENCIAS)
    if len(temporarios) != esperado:
        raise RuntimeError(
            f"Esperados {esperado} Parquets validados; encontrados {len(temporarios)}."
        )

    destino_layout.parent.mkdir(parents=True, exist_ok=True)
    backup = source_dir / f".backup_otimizado_{os.getpid()}"
    if backup.exists():
        raise FileExistsError(
            f"Backup temporário já existe e foi preservado: {backup}. "
            "Verifique-o antes de tentar outra promoção."
        )

    havia_destino = destino_layout.exists()
    if havia_destino:
        os.replace(destino_layout, backup)

    try:
        os.replace(staging_layout, destino_layout)
    except Exception:
        if havia_destino and backup.exists() and not destino_layout.exists():
            os.replace(backup, destino_layout)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def executar(uf: str, force: bool = False, dry_run: bool = False) -> int:
    uf = normalizar_uf(uf)
    raiz = Path(__file__).resolve().parent
    source_dir = raiz / "data" / "consumo" / f"uf={uf}"

    LOG.info("UF solicitada: %s", uf)
    LOG.info("Diretório de dados: %s", source_dir)
    LOG.info(
        "PyArrow=%s | pandas=%s | Memory Pool=%s",
        pa.__version__,
        pd.__version__,
        pa.default_memory_pool().backend_name,
    )

    originais, codigo = validar_originais(source_dir)
    if codigo:
        return codigo
    assert originais is not None

    completo, existentes, manifesto = estado_saida(source_dir, uf)
    destino_layout = source_dir / LAYOUT_OTIMIZADO

    if completo and not force:
        LOG.info(
            "Os dados da UF %s já foram preparados. Foram encontrados os oito "
            "Parquets e o manifesto em %s. Use --force para reprocessar.",
            uf,
            destino_layout,
        )
        return 0

    if (existentes or manifesto.exists()) and not force:
        total = len(caminhos_saida(source_dir))
        LOG.error(
            "A preparação anterior está incompleta: %s de %s Parquets encontrados.",
            len(existentes),
            total,
        )
        for caminho in existentes:
            LOG.error("  existente: %s", caminho.relative_to(source_dir))
        if not manifesto.is_file():
            LOG.error("  manifesto ausente: %s", manifesto.relative_to(source_dir))
        else:
            LOG.error("  manifesto ausente, inválido ou sem validação completa")
        LOG.error("Execute novamente com --force para recriar o conjunto completo.")
        return 2

    if dry_run:
        LOG.info("DRY-RUN: os quatro originais foram encontrados e validados.")
        LOG.info("Seriam gerados oito Parquets em: %s", destino_layout)
        LOG.info("Nenhum arquivo foi criado ou alterado.")
        return 0

    staging_root = Path(
        tempfile.mkdtemp(prefix=f".preparacao_{uf}_", dir=source_dir)
    )
    staging_layout = staging_root / LAYOUT_OTIMIZADO
    staging_layout.mkdir(parents=True, exist_ok=True)

    try:
        registros: list[dict[str, Any]] = []
        for base, origem in originais.items():
            LOG.info("=" * 68)
            registros.extend(transformar_base(base, origem, staging_layout))

        manifesto_dados = {
            "versao_preparador": VERSAO_PREPARADOR,
            "uf": uf,
            "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
            "origem": str(Path("data") / "consumo" / f"uf={uf}"),
            "arquivos_originais": informacoes_origem(originais),
            "configuracao": {
                "layout": LAYOUT_OTIMIZADO,
                "row_group_size": ROW_GROUP_SIZE,
                "compression": "snappy",
                "use_dictionary": True,
                "use_threads": False,
                "downcast_na_gravacao": False,
                "normalizacao_referencia": {"RESIDENCIA": "ESC"},
                "referencias": list(REFERENCIAS),
            },
            "colunas_projetadas": COLUNAS,
            "arquivos_gerados": registros,
            "validacao_geral": {
                "quantidade_arquivos": len(registros),
                "todos_validos": len(registros) == 8
                and all(item["validacao"] == "OK" for item in registros),
            },
        }
        manifesto_path = staging_layout / NOME_MANIFESTO
        manifesto_path.write_text(
            json.dumps(manifesto_dados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        promover_resultados(staging_layout, destino_layout, source_dir)

        LOG.info("=" * 68)
        LOG.info("PREPARAÇÃO CONCLUÍDA | UF=%s | %s Parquets validados", uf, len(registros))
        LOG.info("Destino: %s", destino_layout)
        LOG.info("Manifesto: %s", destino_layout / NOME_MANIFESTO)
        LOG.info("Os quatro Parquets originais foram preservados.")
        return 0
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepara os Parquets de uma UF para o Dashboard ENEM. "
            "Informe explicitamente a sigla com --uf."
        )
    )
    parser.add_argument("--uf", required=True, help="Sigla da UF a preparar (ex.: PA).")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocessa os dados e substitui o conjunto otimizado existente.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verifica os arquivos e mostra o que seria feito, sem gravar nada.",
    )
    return parser


def main() -> int:
    configurar_log()
    parser = construir_parser()
    args = parser.parse_args()
    if args.force and args.dry_run:
        parser.error("--force e --dry-run não podem ser usados juntos.")
    try:
        return executar(args.uf, force=args.force, dry_run=args.dry_run)
    except Exception as exc:
        LOG.exception("Falha ao preparar os dados: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
