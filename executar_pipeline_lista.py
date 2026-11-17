#executar_pipeline_lista.py


"""
Orquestrador ENEM: Bronze -> Silver -> Gold -> Analytic -> Consumo.

"""
#update: gold_duplo
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
from enem_pipeline.gold import executar_gold
from enem_pipeline.analytic import executar_camada_analitica
from enem_pipeline.consumo import executar_camada_consumo


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

def main(input_UF) -> int:
    print("=" * 72)
    print("PIPELINE ENEM — BRONZE → SILVER → GOLD → ANALYTIC → CONSUMO")
    print("=" * 72)
    print(f"Projeto: {ROOT}")

    uf=input_UF
    ano_ini = 1998
    ano_fim = 2025

    print("--" * 36)

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

    BRASIL = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
               "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC",
               "SP","SE","TO"]
    NORTE= ["AC","AM","RO","RR","TO"] #ok
    NORDESTE= ["MA","CE","PI","RN","PB","PE","AL","SE","BA"]
    SUDESTE= ["MG","SP","RJ","ES"] #ok
    CENTROESTE= ["MT","GO","MS","DF"]
    SUL=["RS"]


    for UF in SUL:
        main(UF)
    raise SystemExit(main())
