from pathlib import Path
import sys
from IPython.display import display

diretorio_atual = Path.cwd().resolve()

if diretorio_atual.name in {"notebook", "notebooks"}:
    raiz_projeto = diretorio_atual.parent
else:
    raiz_projeto = diretorio_atual

src_dir = raiz_projeto / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
