"""Diagnóstico de desempenho: mostra no terminal (python app.py) o que o dashboard está fazendo.

Uso:
    from dash_utils.perf import configurar_logs, etapa, medir_callback

    configurar_logs()                      # uma vez, no início do app.py

    with etapa("mapa: montar figura", uf="PA"):
        ...                                # imprime duração ao terminar

    @app.callback(...)
    @medir_callback("atualizar_mapa")      # logo abaixo do @app.callback
    def atualizar_mapa(...):
        ...

Para silenciar tudo:  ENEM_PERF=0 python app.py
Para ver também os argumentos dos callbacks:  ENEM_PERF=2 python app.py
"""
import functools
import itertools
import logging
import os
import sys
import time
import traceback
from contextlib import contextmanager

LOG = logging.getLogger("enem")
_contador = itertools.count(1)
_NIVEL = os.environ.get("ENEM_PERF", "1")


def configurar_logs():
    """Envia os logs do projeto para o terminal, com hora e sem duplicar linhas."""
    if _NIVEL == "0":
        LOG.setLevel(logging.CRITICAL)
        return
    if not LOG.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S"))
        LOG.addHandler(h)
    LOG.setLevel(logging.INFO)
    LOG.propagate = False


def _fmt(seg):
    return f"{seg * 1000:,.0f} ms".replace(",", ".") if seg < 1 else f"{seg:,.2f} s"


@contextmanager
def etapa(nome, **info):
    """Mede um trecho de código e imprime a duração (e informações extras)."""
    ini = time.perf_counter()
    try:
        yield
    finally:
        extra = "  " + " ".join(f"{k}={v}" for k, v in info.items()) if info else ""
        LOG.info("    · %-42s %10s%s", nome, _fmt(time.perf_counter() - ini), extra)


def medir_callback(nome):
    """Decorator para callbacks do Dash: numera cada execução e mede o tempo total.

    Se o mesmo callback aparecer duas vezes seguidas para uma única ação na tela,
    ele está sendo disparado em duplicidade (ver a numeração #N).
    """
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            n = next(_contador)
            detalhe = ""
            if _NIVEL == "2":
                detalhe = " " + ", ".join(repr(a)[:40] for a in args)
            LOG.info("▶ #%d %s%s", n, nome, detalhe)
            ini = time.perf_counter()
            try:
                resultado = func(*args, **kwargs)
            except Exception as exc:
                LOG.info("✖ #%d %s FALHOU em %s: %s: %s", n, nome,
                         _fmt(time.perf_counter() - ini), type(exc).__name__, exc)
                LOG.info(traceback.format_exc())
                raise
            LOG.info("■ #%d %s concluído em %s", n, nome,
                     _fmt(time.perf_counter() - ini))
            return resultado
        return wrapper
    return deco
