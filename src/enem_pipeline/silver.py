#silver.py
from pathlib import Path
import duckdb

from typing import Optional

from enem_pipeline.config import (BRONZE_DIR, SILVER_DIR, STAGING_DIR, UF_PROCESSAMENTO,
    SEPARADOR_MICRODADOS, obter_codificacao_microdados, obter_diretorio_uf, normalizar_uf)

from enem_pipeline.catalogo import obter_variaveis_ano
from enem_pipeline.bronze import inspecionar_esquema_csv
from enem_pipeline.bronze import (selecionar_csvs_dados,extrair_csvs_ano)

from zipfile import ZipFile

# ============================================================
#  1-processar_csv_silver
# ============================================================

def processar_csv_silver(caminho_csv, ano: int, nome_saida: str, coluna_uf: Optional[str] = None, uf: Optional[str] = None) -> dict:
    """
    Seleciona variáveis disponíveis, filtra a UF e grava em Parquet.

    Retorna informações básicas sobre o processamento.
    """
    uf = normalizar_uf(uf)
    caminho_csv = Path(caminho_csv).resolve()

    colunas_origem = inspecionar_esquema_csv(caminho_csv, ano)
    variaveis_catalogo = obter_variaveis_ano(ano)

    if coluna_uf is None:
        coluna_uf = obter_coluna_territorial(ano)

    colunas_selecionadas = [
        coluna
        for coluna in variaveis_catalogo
        if coluna in colunas_origem
    ]

    if coluna_uf not in colunas_origem:
        raise ValueError(
            f"A coluna territorial '{coluna_uf}' não existe no arquivo "
            f"'{caminho_csv.name}' para o ano {ano}. "
            f"Verifique a regra territorial aplicada."
        )

    if coluna_uf not in colunas_selecionadas:
        colunas_selecionadas.append(coluna_uf)

    if not colunas_selecionadas:
        raise ValueError(
            f"Nenhuma variável do catálogo disponível em {caminho_csv.name}."
        )

    diretorio_saida = obter_diretorio_uf(SILVER_DIR, uf) / f"ano={ano}"
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    caminho_saida = diretorio_saida / nome_saida
    caminho_sql = caminho_csv.as_posix().replace("'", "''")
    saida_sql = caminho_saida.as_posix().replace("'", "''")
    separador_sql = SEPARADOR_MICRODADOS.replace("'", "''")
    codificacao = obter_codificacao_microdados(ano)

    selecao_sql = ", ".join(
        '"' + coluna.replace('"', '""') + '"'
        for coluna in colunas_selecionadas
    )

    con = duckdb.connect()

    try:
        con.execute(
            f"""
            COPY (
                SELECT {selecao_sql}
                FROM read_csv(
                    '{caminho_sql}',
                    delim='{separador_sql}',
                    header=true,
                    encoding='{codificacao}',
                    sample_size=20000
                )
                WHERE "{coluna_uf}" = '{uf}'
            )
            TO '{saida_sql}'
            (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )

        total_silver = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{saida_sql}')"
        ).fetchone()[0]

    finally:
        con.close()

    return {
        "ano": ano,
        "arquivo_origem": caminho_csv.name,
        "arquivo_saida": str(caminho_saida),
        "uf": uf,
        "colunas_gravadas": len(colunas_selecionadas),
        "colunas_ausentes_do_catalogo": [
            coluna
            for coluna in variaveis_catalogo
            if coluna not in colunas_origem
        ],
        "colunas_origem_fora_catalogo": [
            coluna
            for coluna in colunas_origem
            if coluna not in variaveis_catalogo
        ],
        "total_registros": total_silver,
    }

# ============================================================
#  2-obter_coluna_territorial
# ============================================================
def obter_coluna_territorial(ano: int) -> str:
    """Retorna a referência territorial correta para cada período."""

    if 1998 <= ano <= 2000:
        return "SG_UF_RESIDENCIA"

    if 2001 <= ano <= 2007:
        return "SG_UF_ESC"

    if 2008 <= ano <= 2025:
        return "SG_UF_PROVA"

    raise ValueError(f"Ano fora do escopo: {ano}")


# ============================================================
#  3-obter_nome_saida_silver
# ============================================================

def obter_nome_saida_silver(caminho_csv, ano: int) -> str:
    """Define o nome do Parquet Silver a partir do arquivo de origem."""
    nome = caminho_csv.stem.upper()

    if ano >= 2024:
        if nome == f"PARTICIPANTES_{ano}":
            return "participantes.parquet"

        if nome == f"RESULTADOS_{ano}":
            return "resultados.parquet"

        raise ValueError(
            f"Arquivo não reconhecido para o ano {ano}: {caminho_csv.name}"
        )

    return f"enem_{ano}.parquet"


# ============================================================
#  4-validar_parquet_silver
# ============================================================


def validar_parquet_silver(caminho_parquet, ano: int, uf: Optional[str] = None) -> dict:
    """Valida leitura, registros, UF e ano do Parquet Silver."""

    uf = normalizar_uf(uf)
    caminho_parquet = Path(caminho_parquet)

    if not caminho_parquet.is_file():
        raise FileNotFoundError(
            f"Parquet não encontrado: {caminho_parquet}"
        )

    if caminho_parquet.stat().st_size == 0:
        raise ValueError(
            f"Parquet vazio: {caminho_parquet}"
        )

    caminho_sql = caminho_parquet.as_posix().replace("'", "''")
    con = duckdb.connect()

    try:
        total = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{caminho_sql}')"
        ).fetchone()[0]

        colunas = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{caminho_sql}')"
        ).fetchdf()["column_name"].tolist()

        if total == 0:
            raise ValueError(
                f"Parquet sem registros: {caminho_parquet}"
            )

        coluna_uf = obter_coluna_territorial(ano)

        if coluna_uf not in colunas:
            raise ValueError(
                f"Coluna territorial '{coluna_uf}' ausente em "
                f"{caminho_parquet.name}."
            )

        uf_incorreta = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{caminho_sql}')
            WHERE "{coluna_uf}" IS DISTINCT FROM ?
            """,
            [uf],
        ).fetchone()[0]

        if uf_incorreta:
            raise ValueError(
                f"{uf_incorreta} registros com UF incorreta em "
                f"{caminho_parquet.name}."
            )

        ano_incorreto = None

        if "NU_ANO" in colunas:
            ano_incorreto = con.execute(
                f"""
                SELECT COUNT(*)
                FROM read_parquet('{caminho_sql}')
                WHERE TRY_CAST(NU_ANO AS INTEGER) IS DISTINCT FROM ?
                """,
                [ano],
            ).fetchone()[0]

            if ano_incorreto:
                raise ValueError(
                    f"{ano_incorreto} registros com ano incorreto em "
                    f"{caminho_parquet.name}."
                )

        return {
            "arquivo_saida": str(caminho_parquet),
            "total_registros": total,
            "colunas_gravadas": len(colunas),
            "uf_incorreta": uf_incorreta,
            "ano_incorreto": ano_incorreto,
            "validado": True,
        }

    finally:
        con.close()




# ============================================================
#  5-processar_ano_silver
# ============================================================




def processar_ano_silver(
    ano: int,
    reprocessar: bool = False,
    limpar_staging: bool = True,
    uf: Optional[str] = None,
) -> list[dict]:
    """
    Extrai, processa, valida e limpa os CSVs de um ano.

    A limpeza ocorre somente após a validação do Parquet.
    Em caso de falha, o CSV é preservado.
    """

    uf = normalizar_uf(uf)
    arquivos_internos = selecionar_csvs_dados(ano)

    if not arquivos_internos:
        raise ValueError(
            f"Nenhum CSV principal identificado para {ano}."
        )

    diretorio_saida = obter_diretorio_uf(SILVER_DIR, uf) / f"ano={ano}"
    resultados = []

    for nome_interno in arquivos_internos:
        nome_csv = Path(nome_interno).name
        caminho_csv = STAGING_DIR / f"ano={ano}" / nome_csv
        nome_saida = obter_nome_saida_silver(caminho_csv, ano)
        caminho_parquet = diretorio_saida / nome_saida

        try:
            # Reutiliza Parquet somente depois de validá-lo.
            if caminho_parquet.is_file() and not reprocessar:
                try:
                    validacao = validar_parquet_silver(
                        caminho_parquet, ano, uf=uf
                    )

                    resultado = {
                        "ano": ano,
                        "arquivo_origem": nome_csv,
                        **validacao,
                        "status": "ja_existente_validado",
                    }

                    if limpar_staging and caminho_csv.is_file():
                        caminho_csv.unlink()
                        resultado["csv_removido"] = True
                    else:
                        resultado["csv_removido"] = False

                    resultados.append(resultado)
                    print(
                        f"Parquet existente validado: {caminho_parquet}"
                    )
                    continue

                except Exception as erro_validacao:
                    print(
                        f"Parquet existente inválido em {ano}: "
                        f"{erro_validacao}"
                    )
                    print("Será reprocessado a partir do CSV.")

            # Extrai se o CSV não existir ou tiver tamanho divergente.
            if not caminho_csv.is_file():
                extrair_csvs_ano(ano)

            if not caminho_csv.is_file():
                raise FileNotFoundError(
                    f"CSV esperado não encontrado no staging: {caminho_csv}"
                )

            # Se a extração detectar tamanho divergente, ela o corrige.
            # Confere novamente o tamanho esperado no ZIP.
            caminho_zip = (
                BRONZE_DIR / f"microdados_enem_{ano}.zip"
            )

            with ZipFile(caminho_zip, "r") as arquivo_zip:
                info = arquivo_zip.getinfo(nome_interno)

            if caminho_csv.stat().st_size != info.file_size:
                extrair_csvs_ano(ano)

            if caminho_csv.stat().st_size != info.file_size:
                raise IOError(
                    f"CSV com tamanho divergente após extração: {caminho_csv}"
                )

            # Evita reaproveitar um Parquet inválido durante a gravação.
            if caminho_parquet.exists():
                caminho_parquet.unlink()

            resultado = processar_csv_silver(
                caminho_csv=caminho_csv,
                ano=ano,
                nome_saida=nome_saida,
                uf=uf,
            )

            validacao = validar_parquet_silver(
                caminho_parquet, ano, uf=uf
            )

            resultado.update(validacao)
            resultado["status"] = "processado_validado"
            resultado["csv_removido"] = False

            # Limpa somente depois de validar o Parquet.
            if limpar_staging:
                caminho_csv.unlink()
                resultado["csv_removido"] = True

            resultados.append(resultado)

        except Exception as erro:
            print(
                f"Falha no ano {ano}, arquivo {nome_csv}: "
                f"{type(erro).__name__}: {erro}"
            )
            raise

    return resultados

