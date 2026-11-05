#features_names.py
from pathlib import Path
import sys
from IPython.display import display

diretorio_atual = Path.cwd().resolve()

if diretorio_atual.name in {"utils"}:
    raiz_projeto = diretorio_atual.parent
else:
    raiz_projeto = diretorio_atual

src_dir = raiz_projeto

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))



import unicodedata
import pandas as pd
import geopandas as gpd

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


# REGRA 2: CRIAR MAPA DE NOMES e atualizar base
def update_nomes(df, df_shape):
    """Atualiza e harmoniza os nomes dos municípios no DataFrame de destino com
        base nos nomes oficiais contidos na malha geográfica (shapefile).

        O cruzamento é realizado de forma exata utilizando o geocódigo do município
        (CD_MUN -> CO_MUNICIPIO_TERRITORIO) como chave primária, garantindo a
        correção de divergências ortográficas ou de grafia
        """
    df["NO_MUNICIPIO_TERRITORIO"] = df["NO_MUNICIPIO_TERRITORIO"].apply(normalizar_nome)
    df_shape["NM_MUN"] = df_shape["NM_MUN"].apply(normalizar_nome)

    mapa_nomes = (df_shape.drop_duplicates(subset=["CD_MUN"])
                  .set_index("CD_MUN")["NM_MUN"].to_dict())

    df["NO_MUNICIPIO_TERRITORIO"] = df["CO_MUNICIPIO_TERRITORIO"].map(mapa_nomes)
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



#
#     return

if __name__ == "__main__":
    UF='PA'
    read_allfiles(UF)
