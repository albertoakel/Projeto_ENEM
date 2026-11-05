#bronze.py
import os
import re
from enem_pipeline.config import BRONZE_DIR, ANO_INICIAL, ANO_FINAL,STAGING_DIR
from enem_pipeline.config import (SEPARADOR_MICRODADOS,obter_codificacao_microdados)

from zipfile import ZipFile, BadZipFile
from pathlib import Path

import duckdb



PADRAO_ARQUIVO = re.compile(r"^microdados_enem_(\d{4})\.zip$")

# ============================================================
#  1-inventariar_bronze
# ============================================================

def inventariar_bronze():
    """Lista os ZIPs do ENEM e identifica os anos disponíveis."""

    arquivos = []

    for caminho in sorted(BRONZE_DIR.glob("*.zip")):
        correspondencia = PADRAO_ARQUIVO.match(caminho.name)

        if correspondencia is None:
            continue

        ano = int(correspondencia.group(1))

        arquivos.append({
            "ano": ano,
            "arquivo": caminho.name,
            "caminho": caminho,
            "tamanho_mb": round(caminho.stat().st_size / (1024 ** 2), 2),
            "ano_no_intervalo": ANO_INICIAL <= ano <= ANO_FINAL,
        })

    return arquivos

# ============================================================
# 2-inspecionar_zip
# ============================================================

def inspecionar_zip(ano):
    """Lista os arquivos internos de um ZIP anual sem extraí-los."""

    caminho_zip = BRONZE_DIR / f"microdados_enem_{ano}.zip"

    if not caminho_zip.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_zip}")

    try:
        with ZipFile(caminho_zip, "r") as arquivo_zip:
            membros = []

            for item in arquivo_zip.infolist():
                if item.is_dir():
                    continue

                membros.append({
                    "nome": item.filename,
                    "tamanho_mb": round(item.file_size / (1024 ** 2), 2),
                    "compactado_mb": round(item.compress_size / (1024 ** 2), 2),
                })

            return membros

    except BadZipFile as erro:
        raise ValueError(f"ZIP inválido: {caminho_zip}") from erro

# ============================================================
# 3-selecionar_csvs_dados
# ============================================================

def selecionar_csvs_dados(ano):
    membros = inspecionar_zip(ano)
    selecionados = []

    for item in membros:
        nome = item["nome"].replace("\\", "/")
        nome_upper = nome.upper()
        nome_base = nome_upper.rsplit("/", 1)[-1]

        if not nome_upper.endswith(".CSV"):
            continue

        if ano <= 2023:
            if nome_base == f"MICRODADOS_ENEM_{ano}.CSV":
                selecionados.append(nome)

        else:
            if nome_base in {
                f"PARTICIPANTES_{ano}.CSV",
                f"RESULTADOS_{ano}.CSV",
            }:
                selecionados.append(nome)

    return selecionados



# ============================================================
# 4-extrair_csvs_ano
 # ============================================================

def extrair_csvs_ano(ano):
    """Extrai CSVs principais para staging e confere o tamanho extraído."""

    arquivos = selecionar_csvs_dados(ano)

    if not arquivos:
        raise ValueError(f"Nenhum CSV principal identificado para {ano}.")

    destino = STAGING_DIR / f"ano={ano}"
    destino.mkdir(parents=True, exist_ok=True)

    caminho_zip = BRONZE_DIR / f"microdados_enem_{ano}.zip"
    extraidos = []

    with ZipFile(caminho_zip, "r") as arquivo_zip:
        for nome_interno in arquivos:
            info = arquivo_zip.getinfo(nome_interno)
            nome_saida = Path(nome_interno).name
            caminho_saida = destino / nome_saida
            caminho_temp = caminho_saida.with_name(
                caminho_saida.name + ".tmp"
            )

            # Reutiliza somente se o tamanho corresponder ao ZIP.
            if (
                caminho_saida.is_file()
                and caminho_saida.stat().st_size == info.file_size
            ):
                print(
                    f"CSV existente com tamanho compatível: {caminho_saida}"
                )
                continue

            if caminho_saida.exists():
                print(
                    f"CSV ausente ou com tamanho divergente; "
                    f"será reextraído: {caminho_saida}"
                )

            # Remove apenas um temporário abandonado de execução anterior.
            caminho_temp.unlink(missing_ok=True)

            try:
                with arquivo_zip.open(info, "r") as origem:
                    with caminho_temp.open("wb") as saida:
                        while True:
                            bloco = origem.read(8 * 1024 * 1024)

                            if not bloco:
                                break

                            saida.write(bloco)

                tamanho_extraido = caminho_temp.stat().st_size

                if tamanho_extraido != info.file_size:
                    raise IOError(
                        f"Extração incompleta de {nome_interno}: "
                        f"esperados {info.file_size:,} bytes, "
                        f"obtidos {tamanho_extraido:,} bytes."
                    )

                # Só substitui o destino após conferir o tamanho.
                os.replace(caminho_temp, caminho_saida)

                extraidos.append(caminho_saida)
                print(
                    f"Extraído e conferido: {caminho_saida} "
                    f"({tamanho_extraido:,} bytes)"
                )

            except Exception:
                caminho_temp.unlink(missing_ok=True)
                raise

    return extraidos



# ============================================================
# 5-validar_csvs_extraidos
# ============================================================

def validar_csvs_extraidos(ano):
    """Compara o tamanho dos CSVs extraídos com os tamanhos no ZIP."""

    arquivos = selecionar_csvs_dados(ano)
    caminho_zip = BRONZE_DIR / f"microdados_enem_{ano}.zip"
    diretorio = STAGING_DIR / f"ano={ano}"

    resultados = []

    with ZipFile(caminho_zip, "r") as arquivo_zip:
        for nome_interno in arquivos:
            nome_saida = Path(nome_interno).name
            caminho_saida = diretorio / nome_saida

            info_zip = arquivo_zip.getinfo(nome_interno)

            existe = caminho_saida.is_file()
            tamanho_extraido = (
                caminho_saida.stat().st_size if existe else None
            )

            valido = (
                existe
                and tamanho_extraido == info_zip.file_size
            )

            resultados.append({
                "arquivo": nome_saida,
                "existe": existe,
                "tamanho_esperado": info_zip.file_size,
                "tamanho_extraido": tamanho_extraido,
                "valido": valido,
            })

    return resultados

# ============================================================
# 6-inspecionar_esquema_csv
# ============================================================


def inspecionar_esquema_csv(caminho, ano: int) -> list[str]:
    """Retorna os nomes das colunas de um CSV sem carregar seus dados."""
    caminho = caminho.as_posix().replace("'", "''")
    separador = SEPARADOR_MICRODADOS.replace("'", "''")
    codificacao = obter_codificacao_microdados(ano)

    con = duckdb.connect()
    try:
        resultado = con.execute(
            f"""
            DESCRIBE
            SELECT *
            FROM read_csv(
                '{caminho}',
                delim='{separador}',
                header=true,
                encoding='{codificacao}',
                sample_size=20000
            )
            """
        ).fetchdf()

        return resultado["column_name"].tolist()
    finally:
        con.close()
