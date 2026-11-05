#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestrador ENEM: Bronze -> Silver -> Gold -> Analytic -> Consumo.

Uso:
    python executar_pipeline.py
Informe UF, ano inicial e ano final no terminal.

O script reutiliza os módulos do projeto. A extração e o processamento Silver
são executados ano a ano para evitar acumular CSVs no staging.
"""
from __future__ import annotations

import sys
import time
import traceback
import shutil
from pathlib import Path

def localizar_raiz() -> Path:
    atual = Path(__file__).resolve().parent
    for candidato in [atual, *atual.parents]:
        if (candidato / "src" / "enem_pipeline" / "config.py").is_file():
            return candidato
    raise FileNotFoundError(
        "Não encontrei src/enem_pipeline/config.py. "
        "Salve este script na raiz do projeto Projeto_ENEM."
    )

ROOT = localizar_raiz()
sys.path.insert(0, str(ROOT / "src"))

from enem_pipeline import config as cfg
from enem_pipeline.bronze import inventariar_bronze, extrair_csvs_ano, validar_csvs_extraidos
from enem_pipeline.silver import processar_ano_silver
from enem_pipeline.analytic import executar_camada_analitica
from enem_pipeline.consumo import executar_camada_consumo

import duckdb
import pandas as pd

def perguntar_uf() -> str:
    siglas = {
        "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
        "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC",
        "SP","SE","TO"
    }
    while True:
        uf = input("UF (ex.: RR, PA, SP): ").strip().upper()
        if uf in siglas:
            return uf
        print("UF inválida. Informe uma sigla válida de dois caracteres.")

def perguntar_ano(texto: str, padrao: int) -> int:
    while True:
        bruto = input(f"{texto} [{padrao}]: ").strip()
        if not bruto:
            return padrao
        try:
            ano = int(bruto)
            if 1998 <= ano <= 2025:
                return ano
        except ValueError:
            pass
        print("Informe um ano inteiro entre 1998 e 2025.")

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def definir_territorio(ano: int) -> dict:
    if 1998 <= ano <= 2000:
        return {"tipo":"RESIDENCIA","codigo":"CO_MUNICIPIO_RESIDENCIA",
                "nome":"NO_MUNICIPIO_RESIDENCIA","uf_codigo":"CO_UF_RESIDENCIA",
                "uf_sigla":"SG_UF_RESIDENCIA"}
    if 2001 <= ano <= 2007:
        return {"tipo":"ESC","codigo":"CO_MUNICIPIO_ESC","nome":"NO_MUNICIPIO_ESC",
                "uf_codigo":"CO_UF_ESC","uf_sigla":"SG_UF_ESC"}
    if 2008 <= ano <= 2025:
        return {"tipo":"PROVA","codigo":"CO_MUNICIPIO_PROVA","nome":"NO_MUNICIPIO_PROVA",
                "uf_codigo":"CO_UF_PROVA","uf_sigla":"SG_UF_PROVA"}
    raise ValueError(f"Ano fora do escopo: {ano}")

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
    silver_root = cfg.SILVER_DIR / f"uf={uf}"
    gold_root = cfg.GOLD_DIR / f"uf={uf}"
    gold_root.mkdir(parents=True, exist_ok=True)
    fontes = []
    for ano in range(ano_ini, ano_fim + 1):
        bases = [("enem", f"enem_{ano}.parquet")] if ano <= 2023 else [
            ("participantes","participantes.parquet"),("resultados","resultados.parquet")]
        for base, nome in bases:
            path = silver_root / f"ano={ano}" / nome
            if not path.is_file():
                raise FileNotFoundError(f"Silver ausente: {path}")
            fontes.append({"ano":ano,"base":base,"arquivo":str(path)})

    con = duckdb.connect()
    manifest_rows = []
    try:
        for i, fonte in enumerate(fontes, 1):
            ano, base, origem = fonte["ano"], fonte["base"], fonte["arquivo"]
            log(f"Gold [{i}/{len(fontes)}] {ano} | {base}")
            cols = {r[0] for r in con.execute(
                "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning=false)",
                [origem]).fetchall()}
            terr = definir_territorio(ano)
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
                campo(terr["uf_sigla"],"SG_UF_TERRITORIO"),
                campo(terr["uf_codigo"],"CO_UF_TERRITORIO"),
                campo(terr["codigo"],"CO_MUNICIPIO_TERRITORIO"),
                campo(terr["nome"],"NO_MUNICIPIO_TERRITORIO"),
            ]
            select += [campo(c) for c in COLUNAS_GOLD[6:]]
            destino_dir = gold_root / f"ano={ano}" / f"base={base}"
            destino_dir.mkdir(parents=True, exist_ok=True)
            saida = destino_dir / "dados.parquet"
            tmp = destino_dir / "dados_gold_tmp.parquet"
            tmp.unlink(missing_ok=True)
            sql_select = ",\n".join(select)
            tmp_sql = str(tmp).replace("'", "''")
            con.execute(f"""
                COPY (
                    SELECT {sql_select}
                    FROM read_parquet(?, hive_partitioning=false)
                ) TO '{tmp_sql}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """, [origem])
            schema = con.execute(
                "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning=false)",
                [str(tmp)]).fetchall()
            if [r[0] for r in schema] != COLUNAS_GOLD:
                tmp.unlink(missing_ok=True)
                raise RuntimeError(f"Schema Gold inválido em {ano}/{base}")
            tmp.replace(saida)
            manifest_rows.append({
                "camada":"gold","uf":uf,"ano":ano,"base":base,
                "tipo_referencia_territorial":terr["tipo"],
                "unidade_integracao":"ano_municipio","join_individual":False,
                "arquivo":origem,"arquivo_gold":str(saida)
            })
    finally:
        con.close()
    manifest = pd.DataFrame(manifest_rows).sort_values(["ano","base"])
    manifest_path = metadata / f"manifesto_gold_{uf}.csv"
    manifest.to_csv(manifest_path, sep=";", index=False, encoding="utf-8")
    log(f"Manifesto Gold salvo: {manifest_path}")
    return manifest_path

def main() -> int:
    print("=" * 72)
    print("PIPELINE ENEM — BRONZE → SILVER → GOLD → ANALYTIC → CONSUMO")
    print("=" * 72)
    print(f"Projeto: {ROOT}")
    uf = perguntar_uf()
    ano_ini = perguntar_ano("Ano inicial", 1998)
    ano_fim = perguntar_ano("Ano final", 2025)

    # uf = perguntar_uf()
    #ano_ini = 1998
    #ano_fim = 2025

    if ano_ini > ano_fim:
        print("Erro: o ano inicial não pode ser maior que o final.")
        return 2

    metadata = Path(cfg.METADATA_DIR)
    metadata.mkdir(parents=True, exist_ok=True)
    log(f"Configuração: UF={uf} | período={ano_ini}–{ano_fim}")
    log("Aviso: confirme que os ZIPs dos anos solicitados já estão em data/bronze.")

    inicio_total = time.perf_counter()
    etapas = [
        "BRONZE — conferir fontes ZIP e extrair CSVs",
        "SILVER — filtrar UF e gerar Parquets",
        "GOLD — canonicalizar território e schema",
        "ANALYTIC — gerar agregações municipais",
        "CONSUMO — integrar produtos analíticos",
    ]
    try:
        # 1. Bronze: conferir fontes ZIP disponíveis. Os ZIPs são preservados.
        t = time.perf_counter()
        log(f"[1/5] {etapas[0]}")
        inventario = {int(item["ano"]): item for item in inventariar_bronze()}
        ausentes = [ano for ano in range(ano_ini, ano_fim + 1) if ano not in inventario]
        if ausentes:
            raise FileNotFoundError(
                f"ZIPs ausentes em data/bronze para os anos: {ausentes}. "
                "O pipeline não baixa microdados automaticamente."
            )

        # Staging é temporário: Bronze conserva os ZIPs de origem.
        # Limpa resíduos de execuções anteriores antes de iniciar este lote.
        staging_root = Path(cfg.STAGING_DIR)
        staging_root.mkdir(parents=True, exist_ok=True)
        for item in staging_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            elif item.is_file() or item.is_symlink():
                item.unlink()
        log(f"Bronze OK: {len(inventario)} ZIPs inventariados; staging anterior limpo "
            f"({time.perf_counter() - t:.1f}s).")

        # 2. Extração + Silver ano a ano: nunca extrair todo o período de uma vez.
        t = time.perf_counter()
        log(f"[2/5] {etapas[1]}")
        total_anos = ano_fim - ano_ini + 1
        for i, ano in enumerate(range(ano_ini, ano_fim + 1), 1):
            log(f"Ano [{i}/{total_anos}] {ano}: preparando staging")
            staging_ano = staging_root / f"ano={ano}"
            if staging_ano.exists():
                shutil.rmtree(staging_ano)

            log(f"  Bronze: extraindo CSVs principais de {ano}")
            extrair_csvs_ano(ano)
            validacao = validar_csvs_extraidos(ano)
            invalidos = [x["arquivo"] for x in validacao if not x["valido"]]
            if invalidos:
                raise RuntimeError(f"Extração Bronze inválida em {ano}: {invalidos}")

            log(f"  Silver: processando {ano} para UF={uf}")
            resultados = processar_ano_silver(
                ano=ano, reprocessar=False, limpar_staging=True, uf=uf
            )
            for item in resultados:
                log(f"    {item.get('status', 'OK')} | {item.get('arquivo_saida', '')}")

            # Confirma que os CSVs extraídos não ficaram acumulados.
            csvs_restantes = list(staging_ano.glob("*.csv")) if staging_ano.exists() else []
            if csvs_restantes:
                raise RuntimeError(
                    f"Staging não foi limpo após Silver de {ano}: "
                    f"{[p.name for p in csvs_restantes]}"
                )
            log(f"  Ano {ano} concluído; staging sem CSVs residuais.")
        log(f"Bronze + Silver concluídas ano a ano ({time.perf_counter() - t:.1f}s).")

        # 3. Gold
        t = time.perf_counter()
        log(f"[3/5] {etapas[2]}")
        gold_manifest = executar_gold(uf, ano_ini, ano_fim, metadata)
        log(f"Gold concluída ({time.perf_counter()-t:.1f}s).")

        # 4. Analytic
        t = time.perf_counter()
        log(f"[4/5] {etapas[3]}")
        resultado_analytic = executar_camada_analitica(
            manifesto_gold_path=gold_manifest,
            metadata_dir=metadata,
            analytic_root=cfg.ANALYTIC_DIR,
            uf=uf, ano_inicial=ano_ini, ano_final=ano_fim, gravar=True,
        )
        log(f"Analytic OK: {len(resultado_analytic['produtos'])} produtos ({time.perf_counter()-t:.1f}s).")

        # 5. Consumo
        t = time.perf_counter()
        log(f"[5/5] {etapas[4]}")
        resultado_consumo = executar_camada_consumo(
            manifesto_analytic_path=metadata / f"manifesto_analytic_{uf}.csv",
            metadata_dir=metadata, consumo_root=cfg.CONSUMO_DIR,
            uf=uf, gravar=True,
        )
        if not resultado_consumo.get("auditoria_ok", False):
            display = resultado_consumo.get("auditoria")
            raise RuntimeError(f"Auditoria Consumo falhou:\n{display}")
        log(f"Consumo OK: {len(resultado_consumo['produtos'])} produtos ({time.perf_counter()-t:.1f}s).")

        total = time.perf_counter() - inicio_total
        log("=" * 72)
        log(f"PIPELINE CONCLUÍDO | UF={uf} | {ano_ini}–{ano_fim} | {total/60:.1f} min")
        log(f"Relatórios/metadados em: {metadata}")
        log("=" * 72)
        return 0
    except Exception as exc:
        log(f"PIPELINE INTERROMPIDO: {type(exc).__name__}: {exc}")
        log("Etapas anteriores permanecem gravadas; corrija a causa antes de retomar.")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()
    raise SystemExit(main())

    # UF = ['RS']
    # for i in UF:
    #     main(i)
    #raise SystemExit(main())
