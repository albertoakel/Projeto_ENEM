from pathlib import Path
import sys
import warnings
from matplotlib.ticker import PercentFormatter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import seaborn as sns

from IPython.display import display

diretorio_atual = Path.cwd().resolve()

if diretorio_atual.name.lower() == "estudos_analiticos":
    raiz_projeto = diretorio_atual.parent.parent
else:
    raiz_projeto = diretorio_atual

src_dir = raiz_projeto / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from enem_pipeline.config import (
    PROJECT_ROOT,
    DATA_DIR,
    CONSUMO_DIR,
    UF_PROCESSAMENTO,
    ANO_INICIAL,
    ANO_FINAL,
)

from utils.features_names import read_allfiles2
from utils import eda2



warnings.filterwarnings("ignore", category=FutureWarning)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)

sns.set_theme(style="whitegrid", context="talk")
palette = sns.color_palette("tab10", n_colors=8)

plt.rcParams["figure.figsize"] = (12, 5)
plt.rcParams["figure.dpi"] = 110

