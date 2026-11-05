#catalogo.py
import pandas as pd

from enem_pipeline.config import DICIONARIOS_DIR


ARQUIVO_CATALOGO = DICIONARIOS_DIR / "variaveis_enem_por_ano.csv"


def carregar_catalogo() -> pd.DataFrame:
    """Carrega o catálogo de variáveis disponíveis por ano."""
    if not ARQUIVO_CATALOGO.is_file():
        raise FileNotFoundError(
            f"Catálogo não encontrado: {ARQUIVO_CATALOGO}"
        )

    catalogo = pd.read_csv(
        ARQUIVO_CATALOGO,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
    )

    catalogo.columns = catalogo.columns.map(str).str.strip()

    return catalogo


def obter_variaveis_ano(ano: int) -> list[str]:
    """Retorna as variáveis não nulas disponíveis em determinado ano."""
    catalogo = carregar_catalogo()
    coluna = str(ano)

    if coluna not in catalogo.columns:
        raise ValueError(
            f"O ano {ano} não existe no catálogo."
        )

    variaveis = (
        catalogo[coluna]
        .dropna()
        .astype(str)
        .str.strip()
    )

    variaveis = variaveis[variaveis != ""]

    if variaveis.empty:
        raise ValueError(
            f"Nenhuma variável encontrada para o ano {ano}."
        )

    return variaveis.tolist()
