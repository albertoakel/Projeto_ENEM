#data_loader.py
import logging
import os
import sys
import threading
import time
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

# Diretórios do projeto
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
SRC_DIR = RAIZ_PROJETO / "src"

# Configuração do PROJ
PROJ_DIR = Path(sys.prefix) / "share" / "proj"

os.environ["PROJ_DATA"] = str(PROJ_DIR)
os.environ["PROJ_LIB"] = str(PROJ_DIR)

# Disponibiliza os módulos do projeto
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from utils.features_names import read_allfiles2

LOG = logging.getLogger("enem.cache")
_TABELAS = ("painel", "faixa", "grupo", "dsp")


# O Dash atende callbacks em paralelo (threads). Com lru_cache, três callbacks que pedem
# a mesma UF ao mesmo tempo liam o disco três vezes (visto no log: MG levou ~3 s x3).
# Aqui cada UF tem uma trava: o primeiro lê, os demais esperam e reaproveitam.
_TRAVAS = {}
_TRAVAS_GUARDA = threading.Lock()


def _trava(chave):
    with _TRAVAS_GUARDA:
        return _TRAVAS.setdefault(chave, threading.Lock())


_CACHE_UF = OrderedDict()
_MAX_UFS = 3


def _carregar_uf(uf):
    """Lê do disco UMA vez por UF (parquets + shapefile), com ESC e PROVA juntos."""
    with _trava(("uf", uf)):
        if uf in _CACHE_UF:
            _CACHE_UF.move_to_end(uf)
            return _CACHE_UF[uf]
        LOG.info("CACHE MISS  UF=%s -> lendo do disco...", uf)
        ini = time.perf_counter()
        dados = read_allfiles2(uf, P=None)
        LOG.info("CACHE MISS  UF=%s -> leitura completa em %.2f s", uf, time.perf_counter() - ini)
        _CACHE_UF[uf] = {
            "painel": dados["painel"]["data"],
            "faixa": dados["faixa"]["data"],
            "grupo": dados["grupo"]["data"],
            "dsp": dados["dsp"]["data"],
            "shape": dados["shape"]["data"],
        }
        while len(_CACHE_UF) > _MAX_UFS:
            _CACHE_UF.popitem(last=False)
        return _CACHE_UF[uf]


@lru_cache(maxsize=8)
def _carregar_dados_cache(uf, referencia):
    """Filtra ESC/PROVA em memória a partir dos dados da UF (sem reler o disco)."""
    base = _carregar_uf(uf)
    out = {"shape": base["shape"], "referencia": referencia or "ESC & PROVA"}
    outra = {"ESC": "PROVA", "PROVA": "ESC"}.get(referencia)
    for nome in _TABELAS:
        df = base[nome]
        if outra is not None:
            # equivalente ao drop() anterior: remove só a referência não escolhida
            df = df[df["TIPO_REFERENCIA_TERRITORIAL"] != outra].reset_index(drop=True)
        out[nome] = df
    return out


def _copiar_dados(dados):
    """Devolve cópias das tabelas para proteger o cache. O shape é compartilhado
    (somente leitura): copiá-lo a cada callback só custava tempo."""
    return {
        chave: (valor.copy(deep=True) if chave in _TABELAS else valor)
        for chave, valor in dados.items()
    }


def carregar_dados(uf="PA", referencia=None):
    """
    Carrega os produtos de Consumo e o shapefile de uma unidade da federação.

    Os dados são armazenados em cache por UF e referência territorial.
    Cada chamada devolve cópias dos DataFrames, evitando que alterações feitas
    pelos callbacks contaminem os dados armazenados em memória.

    referencia:
        "ESC"   -> somente ESC
        "PROVA" -> somente PROVA
        None ou qualquer outro valor -> ESC + PROVA
    """
    uf = str(uf).strip().upper()

    if isinstance(referencia, str):
        referencia = referencia.strip().upper()

    if referencia not in ("ESC", "PROVA"):
        referencia = None

    ja_em_memoria = uf in _CACHE_UF
    ini = time.perf_counter()
    dados = _carregar_dados_cache(uf, referencia)
    if ja_em_memoria:
        LOG.info("CACHE HIT   UF=%s ref=%s", uf, referencia or "ESC+PROVA")
    t_cache = time.perf_counter() - ini
    ini = time.perf_counter()
    copia = _copiar_dados(dados)
    LOG.info("    · %-42s %8.0f ms (cache %.0f ms)", "carregar_dados: cópia das tabelas",
             (time.perf_counter() - ini) * 1000, t_cache * 1000)
    return copia


def limpar_cache_dados():
    """Limpa os dados em memória; útil após atualizar os arquivos de Consumo."""
    _carregar_dados_cache.cache_clear()
    _CACHE_UF.clear()
    LOG.info("Cache de dados limpo.")


def status_cache_dados():
    """Retorna estatísticas de uso do cache para diagnóstico."""
    return {"ufs_em_memoria": list(_CACHE_UF), "filtrado": _carregar_dados_cache.cache_info()}
