#gold.py
"""Construção da camada Gold a partir dos arquivos Silver.

Gera um Parquet por ano, base de origem e referência territorial,
padronizando o schema e registrando as saídas no manifesto Gold.
"""
from __future__ import annotations

import time
from pathlib import Path

import duckdb
import pandas as pd

from enem_pipeline import config as cfg


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def definir_territorios(ano: int, base: str) -> list[dict]:
    """Retorna as perspectivas territoriais a gerar para cada fonte Silver."""
    residencia = {
        "tipo": "RESIDENCIA",
        "codigo": "CO_MUNICIPIO_RESIDENCIA",
        "nome": "NO_MUNICIPIO_RESIDENCIA",
        "uf_codigo": "CO_UF_RESIDENCIA",
        "uf_sigla": "SG_UF_RESIDENCIA",
    }
    escola = {
        "tipo": "ESC",
        "codigo": "CO_MUNICIPIO_ESC",
        "nome": "NO_MUNICIPIO_ESC",
        "uf_codigo": "CO_UF_ESC",
        "uf_sigla": "SG_UF_ESC",
    }
    prova = {
        "tipo": "PROVA",
        "codigo": "CO_MUNICIPIO_PROVA",
        "nome": "NO_MUNICIPIO_PROVA",
        "uf_codigo": "CO_UF_PROVA",
        "uf_sigla": "SG_UF_PROVA",
    }

    if 1998 <= ano <= 2000:
        return [residencia]
    if 2001 <= ano <= 2007:
        return [escola]
    if 2008 <= ano <= 2023:
        return [escola, prova]
    if 2024 <= ano <= 2025:
        if base == "participantes":
            return [prova]
        if base == "resultados":
            return [escola, prova]
    raise ValueError(f"Combinação ano/base fora do escopo: {ano}/{base}")

COLUNAS_GOLD = [
    "NU_ANO","TIPO_REFERENCIA_TERRITORIAL","SG_UF_TERRITORIO",
    "CO_UF_TERRITORIO","CO_MUNICIPIO_TERRITORIO","NO_MUNICIPIO_TERRITORIO",
    "TP_SEXO","TP_FAIXA_ETARIA","ANO_CONCLUIU","TP_PRESENCA",
    "TP_PRESENCA_CN","TP_PRESENCA_CH","TP_PRESENCA_LC","TP_PRESENCA_MT",
    "NU_NOTA_CN","NU_NOTA_CH","NU_NOTA_LC","NU_NOTA_MT","NU_NOTA_OBJETIVA",
    "NU_NOTA_REDACAO","TP_STATUS_REDACAO","VL_PERC_COMP1","VL_PERC_COMP2",
    "VL_PERC_COMP3","VL_PERC_COMP4","VL_PERC_COMP5","CO_ESCOLA","TP_ESCOLA",
    "TP_DEPENDENCIA_ADM_ESC",
]
TIPOS_GOLD = {
    "NU_ANO":"INTEGER","TIPO_REFERENCIA_TERRITORIAL":"VARCHAR",
    "SG_UF_TERRITORIO":"VARCHAR","CO_UF_TERRITORIO":"VARCHAR",
    "CO_MUNICIPIO_TERRITORIO":"VARCHAR","NO_MUNICIPIO_TERRITORIO":"VARCHAR",
    "TP_SEXO":"VARCHAR","TP_FAIXA_ETARIA":"INTEGER","ANO_CONCLUIU":"INTEGER",
    "TP_PRESENCA":"INTEGER","TP_PRESENCA_CN":"INTEGER","TP_PRESENCA_CH":"INTEGER",
    "TP_PRESENCA_LC":"INTEGER","TP_PRESENCA_MT":"INTEGER","NU_NOTA_CN":"DOUBLE",
    "NU_NOTA_CH":"DOUBLE","NU_NOTA_LC":"DOUBLE","NU_NOTA_MT":"DOUBLE",
    "NU_NOTA_OBJETIVA":"DOUBLE","NU_NOTA_REDACAO":"DOUBLE",
    "TP_STATUS_REDACAO":"VARCHAR","VL_PERC_COMP1":"DOUBLE","VL_PERC_COMP2":"DOUBLE",
    "VL_PERC_COMP3":"DOUBLE","VL_PERC_COMP4":"DOUBLE","VL_PERC_COMP5":"DOUBLE",
    "CO_ESCOLA":"VARCHAR","TP_ESCOLA":"INTEGER","TP_DEPENDENCIA_ADM_ESC":"INTEGER",
}

def executar_gold(uf: str, ano_ini: int, ano_fim: int, metadata: Path) -> Path:
    """Gera um arquivo Gold independente para cada referência territorial."""
    silver_root = cfg.SILVER_DIR / f"uf={uf}"
    gold_root = cfg.GOLD_DIR / f"uf={uf}"
    gold_root.mkdir(parents=True, exist_ok=True)

    fontes = []
    for ano in range(ano_ini, ano_fim + 1):
        bases = [("enem", f"enem_{ano}.parquet")] if ano <= 2023 else [
            ("participantes", "participantes.parquet"),
            ("resultados", "resultados.parquet"),
        ]
        for base, nome in bases:
            path = silver_root / f"ano={ano}" / nome
            if not path.is_file():
                raise FileNotFoundError(f"Silver ausente: {path}")
            fontes.append({"ano": ano, "base": base, "arquivo": str(path)})

    con = duckdb.connect()
    manifest_rows = []
    try:
        total_saidas = sum(
            len(definir_territorios(fonte["ano"], fonte["base"]))
            for fonte in fontes
        )
        indice_saida = 0

        for fonte in fontes:
            ano, base, origem = fonte["ano"], fonte["base"], fonte["arquivo"]
            cols = {
                r[0] for r in con.execute(
                    "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning=false)",
                    [origem],
                ).fetchall()
            }
            territorios = definir_territorios(ano, base)

            for terr in territorios:
                indice_saida += 1
                log(
                    f"Gold [{indice_saida}/{total_saidas}] "
                    f"{ano} | {base} | {terr['tipo']}"
                )

                # O código municipal é obrigatório para cada perspectiva.
                # Nome e UF permanecem opcionais para compatibilidade histórica.
                if terr["codigo"] not in cols:
                    raise ValueError(
                        f"Coluna territorial {terr['codigo']} ausente em {ano}/{base}: {origem}"
                    )

                def campo(nome, alias=None):
                    destino = alias or nome
                    if destino not in TIPOS_GOLD:
                        raise KeyError(destino)
                    if nome in cols:
                        return f'CAST("{nome}" AS {TIPOS_GOLD[destino]}) AS "{destino}"'
                    return f'CAST(NULL AS {TIPOS_GOLD[destino]}) AS "{destino}"'

                select = [
                    campo("NU_ANO"),
                    f"CAST('{terr['tipo']}' AS VARCHAR) AS \"TIPO_REFERENCIA_TERRITORIAL\"",
                    campo(terr["uf_sigla"], "SG_UF_TERRITORIO"),
                    campo(terr["uf_codigo"], "CO_UF_TERRITORIO"),
                    campo(terr["codigo"], "CO_MUNICIPIO_TERRITORIO"),
                    campo(terr["nome"], "NO_MUNICIPIO_TERRITORIO"),
                ]
                select += [campo(c) for c in COLUNAS_GOLD[6:]]

                destino_dir = (
                    gold_root / f"ano={ano}" / f"base={base}"
                    / f"referencia={terr['tipo']}"
                )
                destino_dir.mkdir(parents=True, exist_ok=True)
                saida = destino_dir / "dados.parquet"
                tmp = destino_dir / "dados_gold_tmp.parquet"
                tmp.unlink(missing_ok=True)

                sql_select = ",\n".join(select)
                tmp_sql = str(tmp).replace("'", "''")
                con.execute(
                    f"""
                    COPY (
                        SELECT {sql_select}
                        FROM read_parquet(?, hive_partitioning=false)
                    ) TO '{tmp_sql}' (FORMAT PARQUET, COMPRESSION ZSTD)
                    """,
                    [origem],
                )

                schema = con.execute(
                    "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning=false)",
                    [str(tmp)],
                ).fetchall()
                if [r[0] for r in schema] != COLUNAS_GOLD:
                    tmp.unlink(missing_ok=True)
                    raise RuntimeError(
                        f"Schema Gold inválido em {ano}/{base}/{terr['tipo']}"
                    )

                # Confirma que a perspectiva foi gravada sem perda de registros.
                n_origem = con.execute(
                    "SELECT COUNT(*) FROM read_parquet(?)", [origem]
                ).fetchone()[0]
                n_saida = con.execute(
                    "SELECT COUNT(*) FROM read_parquet(?)", [str(tmp)]
                ).fetchone()[0]
                if n_origem != n_saida:
                    tmp.unlink(missing_ok=True)
                    raise RuntimeError(
                        f"Contagem divergente em {ano}/{base}/{terr['tipo']}: "
                        f"Silver={n_origem}, Gold={n_saida}"
                    )

                tmp.replace(saida)
                manifest_rows.append({
                    "camada": "gold",
                    "uf": uf,
                    "ano": ano,
                    "base": base,
                    "tipo_referencia_territorial": terr["tipo"],
                    "unidade_integracao": "ano_municipio_tipo_referencia",
                    "join_individual": False,
                    "arquivo": origem,
                    "arquivo_gold": str(saida),
                    "n_registros": n_saida,
                })
    finally:
        con.close()

    manifest = pd.DataFrame(manifest_rows).sort_values(
        ["ano", "base", "tipo_referencia_territorial"]
    )
    manifest_path = metadata / f"manifesto_gold_{uf}.csv"
    manifest.to_csv(manifest_path, sep=";", index=False, encoding="utf-8")
    log(f"Manifesto Gold salvo: {manifest_path}")
    return manifest_path
