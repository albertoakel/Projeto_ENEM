#config.py
from pathlib import Path
from typing import Optional

# ============================================================
# DIRETÓRIO RAIZ DO PROJETO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ============================================================
# CONFIGURAÇÃO DO PROCESSAMENTO
# ============================================================

UF_PROCESSAMENTO = "PA"  # UF padrão; pode ser sobrescrita nas funções de processamento

ANO_INICIAL = 1998
ANO_FINAL = 2025

ANOS_PROCESSAMENTO = range(
    ANO_INICIAL,
    ANO_FINAL + 1
)

# ============================================================
# DIRETÓRIOS DE DADOS
# ============================================================

DATA_DIR = PROJECT_ROOT / "data"

BRONZE_DIR = DATA_DIR / "bronze"
STAGING_DIR = DATA_DIR / "staging"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
ANALYTIC_DIR = DATA_DIR / "analytic"
CONSUMO_DIR = DATA_DIR / "consumo"

METADATA_DIR = DATA_DIR / "metadata"
DICIONARIOS_DIR = METADATA_DIR / "dicionarios"


def normalizar_uf(uf: Optional[str] = None) -> str:
    """Valida e normaliza a UF; usa UF_PROCESSAMENTO quando não informada."""
    valor = UF_PROCESSAMENTO if uf is None else uf
    valor = str(valor).strip().upper()
    if len(valor) != 2 or not valor.isalpha():
        raise ValueError(f"UF inválida: {uf!r}. Informe a sigla de dois caracteres.")
    return valor


def obter_diretorio_uf(diretorio: Path, uf: Optional[str] = None) -> Path:
    """Retorna o diretório da UF informada ou da UF padrão."""
    return diretorio / f"uf={normalizar_uf(uf)}"

# ============================================================
# FUNÇÕES DE CONFIGURAÇÃO
# ============================================================

SEPARADOR_MICRODADOS = ";"

CODIFICACAO_MICRODADOS_PADRAO = "utf-8"

CODIFICACAO_MICRODADOS_POR_ANO = {
    2006: "latin-1",
    2008: "latin-1",
    2011: "latin-1",
    2012: "latin-1",
    2013: "latin-1",
    2014: "latin-1",
    2015: "latin-1",
    2016: "latin-1",
    2017: "latin-1",
    2018: "latin-1",
    2019: "latin-1",
    2020: "latin-1",
    2021: "latin-1",
    2022: "latin-1",
    2023: "latin-1",
    2024: "latin-1",
    2025: "latin-1",
}


def obter_codificacao_microdados(ano: int) -> str:
    """Retorna a codificação configurada para o ano."""
    return CODIFICACAO_MICRODADOS_POR_ANO.get(
        ano,
        CODIFICACAO_MICRODADOS_PADRAO,
    )




