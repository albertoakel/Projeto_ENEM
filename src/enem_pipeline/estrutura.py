#estrutura.py
from .config import (
    PROJECT_ROOT,
    BRONZE_DIR,
    STAGING_DIR,
    SILVER_DIR,
    GOLD_DIR,
    ANALYTIC_DIR,
    CONSUMO_DIR,
    METADATA_DIR,
    DICIONARIOS_DIR,
)


def verificar_estrutura():
    """Verifica a existência dos diretórios esperados do projeto."""

    diretorios = {
        "raiz": PROJECT_ROOT,
        "bronze": BRONZE_DIR,
        "staging": STAGING_DIR,
        "silver": SILVER_DIR,
        "gold": GOLD_DIR,
        "analytic": ANALYTIC_DIR,
        "consumo": CONSUMO_DIR,
        "metadata": METADATA_DIR,
        "dicionarios": DICIONARIOS_DIR,
    }

    resultado = {}

    for nome, caminho in diretorios.items():
        resultado[nome] = {
            "caminho": str(caminho),
            "existe": caminho.is_dir(),
        }

    return resultado
