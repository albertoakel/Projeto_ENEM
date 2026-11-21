from pathlib import Path
import sys
from IPython.display import display

diretorio_atual = Path.cwd().resolve()

print(f'>>diretorio_atual: {diretorio_atual}')

if diretorio_atual.name in {"pipeline"}:
    raiz_projeto = diretorio_atual.parent.parent
else:
    raiz_projeto = diretorio_atual

src_dir = raiz_projeto / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(1, str(src_dir))