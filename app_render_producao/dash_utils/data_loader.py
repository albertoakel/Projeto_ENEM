# Loader de produção do Dashboard ENEM
import logging
import os
import sys
import threading
import time
from collections import OrderedDict
from pathlib import Path

# Configuração opcional do PROJ.
# Em ambientes Conda o diretório costuma existir em sys.prefix/share/proj.
# Em virtualenvs (como no Render), deixe PyProj localizar os dados do pacote
# quando esse caminho não existir; não force uma pasta ausente.
PROJ_DIR = Path(sys.prefix) / "share" / "proj"
if PROJ_DIR.is_dir():
    os.environ.setdefault("PROJ_DATA", str(PROJ_DIR))
    os.environ.setdefault("PROJ_LIB", str(PROJ_DIR))

# Importação da função de leitura
from .features_names import read_allfiles2, status_loader_otimizado


LOG = logging.getLogger("enem.cache")
LOG.info("Loader otimizado ativo | %s", status_loader_otimizado())

_TABELAS = ("painel", "faixa", "grupo", "dsp")

# Cache único: cada entrada representa uma combinação UF + referência.
_CACHE_DADOS = OrderedDict()
_MAX_ENTRADAS_CACHE = int(os.environ.get("ENEM_CACHE_MAX_ENTRIES", "1"))

# Travas por combinação UF/referência
_TRAVAS = {}
_TRAVAS_GUARDA = threading.Lock()


def _trava(chave):
    with _TRAVAS_GUARDA:
        return _TRAVAS.setdefault(chave, threading.Lock())


def _normalizar_referencia(referencia):
    if isinstance(referencia, str):
        referencia = referencia.strip().upper()

    if referencia not in ("ESC", "PROVA"):
        return None

    return referencia


def _carregar_dados_cache(uf, referencia):
    """
    Carrega diretamente a referência solicitada e mantém
    uma entrada independente no cache para cada UF/referência.
    """
    chave = (uf, referencia)

    with _trava(chave):

        # Verifica o cache
        with _TRAVAS_GUARDA:
            if chave in _CACHE_DADOS:
                _CACHE_DADOS.move_to_end(chave)
                LOG.info(
                    "CACHE HIT | UF=%s ref=%s",
                    uf,
                    referencia or "ESC+PROVA",
                )
                return _CACHE_DADOS[chave]

        # Cache miss: leitura direta da referência solicitada
        LOG.info(
            "CACHE MISS | UF=%s ref=%s -> lendo do disco...",
            uf,
            referencia or "ESC+PROVA",
        )

        inicio = time.perf_counter()

        dados_brutos = read_allfiles2(uf, P=referencia)

        LOG.info(
            "LEITURA CONCLUÍDA | UF=%s ref=%s | tempo=%.2f s",
            uf,
            referencia or "ESC+PROVA",
            time.perf_counter() - inicio,
        )

        dados = {
            "shape": dados_brutos["shape"]["data"],
            "referencia": referencia or "ESC & PROVA",
        }

        # Registra dimensões e memória de cada tabela
        for nome in _TABELAS:
            df = dados_brutos[nome]["data"]

            memoria = (
                df.memory_usage(deep=True).sum() / 1024**2
            )

            LOG.info(
                "LEITURA TABELA | UF=%s ref=%s tabela=%s "
                "| dimensões=%s | memória=%.2f MB",
                uf,
                referencia or "ESC+PROVA",
                nome,
                df.shape,
                memoria,
            )

            dados[nome] = df

        # Armazena a combinação UF/referência
        with _TRAVAS_GUARDA:
            _CACHE_DADOS[chave] = dados
            _CACHE_DADOS.move_to_end(chave)

            while len(_CACHE_DADOS) > _MAX_ENTRADAS_CACHE:
                removida, _ = _CACHE_DADOS.popitem(last=False)

                LOG.info(
                    "CACHE EVICTION | UF=%s ref=%s",
                    removida[0],
                    removida[1] or "ESC+PROVA",
                )

            LOG.info(
                "CACHE STATUS | entradas=%s | limite=%s",
                len(_CACHE_DADOS),
                _MAX_ENTRADAS_CACHE,
            )

        return dados


def _copiar_dados(dados):
    """
    Devolve cópias superficiais dos DataFrames.
    No pandas 3.x, Copy-on-Write protege os dados compartilhados:
    alterações feitas na cópia não contaminam o DataFrame em cache.
    O shapefile é compartilhado e deve ser tratado como somente leitura.
    """
    return {
        chave: (
            valor.copy(deep=False)
            if chave in _TABELAS
            else valor
        )
        for chave, valor in dados.items()
    }


def carregar_dados(uf="PA", referencia=None):
    """
    Carrega dados de Consumo e o shapefile de uma UF.

    referencia:
        "ESC"   -> somente ESC, incluindo registros originalmente RESIDENCIA
        "PROVA" -> somente PROVA
        None    -> ESC + PROVA

    Cada combinação UF/referência é armazenada em um único cache.
    As tabelas são devolvidas como cópias superficiais (Copy-on-Write).
    """
    uf = str(uf).strip().upper()
    referencia = _normalizar_referencia(referencia)

    inicio = time.perf_counter()
    dados_cache = _carregar_dados_cache(uf, referencia)
    tempo_cache = time.perf_counter() - inicio

    inicio = time.perf_counter()
    dados_saida = _copiar_dados(dados_cache)

    LOG.info(
        "    · %-42s %8.0f ms (cache %.0f ms)",
        "carregar_dados: cópia superficial",
        (time.perf_counter() - inicio) * 1000,
        tempo_cache * 1000,
    )

    return dados_saida


def limpar_cache_dados():
    """Limpa os dados em memória."""
    with _TRAVAS_GUARDA:
        _CACHE_DADOS.clear()

    LOG.info("Cache de dados limpo.")


def status_cache_dados():
    """Retorna estatísticas de uso do cache."""
    with _TRAVAS_GUARDA:
        return {
            "entradas_em_memoria": [
                {
                    "uf": uf,
                    "referencia": referencia or "ESC+PROVA",
                }
                for uf, referencia in _CACHE_DADOS.keys()
            ],
            "quantidade": len(_CACHE_DADOS),
            "limite": _MAX_ENTRADAS_CACHE,
        }
