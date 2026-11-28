import os
import time
import json
import logging
from pathlib import Path

from flask import g, request
from datetime import datetime



# ============================================================
# CONFIGURAÇÃO DOS LOGS
# ============================================================

# Pega a data e hora atuais
agora = datetime.now()

data_formatada = agora.strftime("%d%m%Y_%H%M%S")
log_file=f'memoria_dashboard.{data_formatada}.log'

PASTA_LOGS = Path(__file__).resolve().parent / "logs"
PASTA_LOGS.mkdir(exist_ok=True)

ARQUIVO_LOG = PASTA_LOGS / log_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RAM] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
    ],
    force=True,
)

logger = logging.getLogger("RAM")


# ============================================================
# MEDIÇÃO DE MEMÓRIA DO PROCESSO
# ============================================================

def _ler_memoria_linux():
    """
    Retorna RSS, pico de RSS (VmHWM) e USS aproximado, em MB.

    RSS e VmHWM: /proc/self/status
    USS: soma de Private_Clean, Private_Dirty e Private_Hugetlb
         em /proc/self/smaps_rollup.
    """

    memoria = {
        "rss": None,
        "pico_rss": None,
        "uss": None,
    }

    try:
        with open("/proc/self/status", "r") as arquivo:
            for linha in arquivo:
                if linha.startswith("VmRSS:"):
                    memoria["rss"] = int(linha.split()[1]) / 1024
                elif linha.startswith("VmHWM:"):
                    memoria["pico_rss"] = int(linha.split()[1]) / 1024
    except (OSError, ValueError):
        pass

    try:
        with open("/proc/self/smaps_rollup", "r") as arquivo:
            privados_kb = 0

            for linha in arquivo:
                if linha.startswith(
                    ("Private_Clean:", "Private_Dirty:", "Private_Hugetlb:")
                ):
                    privados_kb += int(linha.split()[1])

            memoria["uss"] = privados_kb / 1024
    except (OSError, ValueError):
        pass

    return memoria


def _formatar_memoria(memoria):
    def formatar(valor):
        return f"{valor:.1f} MB" if valor is not None else "N/D"

    return (
        f"RSS={formatar(memoria['rss'])} | "
        f"USS={formatar(memoria['uss'])} | "
        f"Pico RSS={formatar(memoria['pico_rss'])}"
    )


# ============================================================
# IDENTIFICAÇÃO DAS REQUISIÇÕES DO DASH
# ============================================================

ROTULOS_PAGINAS = {
    "/": "visao_geral",
    "/mapas": "mapas",
    "/analise-municipal": "analise_municipal",
    "/perfil-participantes": "perfil_participantes",
}


def _resumir_requisicao_dash():
    """
    Extrai informações do payload enviado pelo Dash.

    O campo 'output' identifica o callback acionado.
    O pathname, quando presente, identifica a página solicitada.
    Os inputs ajudam a identificar UF, referência, ano e disciplina.
    """

    contexto = {
        "pagina": None,
        "callback": None,
        "alterados": None,
        "entradas": [],
    }

    try:
        payload = request.get_json(silent=True) or {}

        contexto["callback"] = payload.get("output")
        contexto["alterados"] = payload.get("changedPropIds")

        for item in payload.get("inputs", []):
            componente = item.get("id")
            propriedade = item.get("property")
            valor = item.get("value")

            if componente == "url" and propriedade == "pathname":
                contexto["pagina"] = ROTULOS_PAGINAS.get(
                    valor, f"rota:{valor}"
                )

            # Registra apenas entradas relevantes para o diagnóstico.
            if componente in {
                "url",
                "seletor-uf",
                "seletor-referencia-territorial",
            }:
                contexto["entradas"].append(
                    f"{componente}.{propriedade}={valor}"
                )

            # Entradas de callbacks das páginas (ano, disciplina etc.).
            elif propriedade == "value":
                contexto["entradas"].append(
                    f"{componente}.{propriedade}={valor}"
                )

        # Alguns callbacks recebem valores em State, não em Input.
        for item in payload.get("state", []):
            componente = item.get("id")
            propriedade = item.get("property")
            valor = item.get("value")

            if propriedade == "value":
                contexto["entradas"].append(
                    f"{componente}.{propriedade}={valor}"
                )

    except Exception as erro:
        contexto["erro_payload"] = str(erro)

    return contexto


# ============================================================
# 1. MEMÓRIA ANTES DE IMPORTAR O DASHBOARD
# ============================================================

memoria_inicial = _ler_memoria_linux()

logger.info("PROCESSO INICIAL")
logger.info(_formatar_memoria(memoria_inicial))


# ============================================================
# 2. IMPORTAÇÃO DA APLICAÇÃO ORIGINAL
# ============================================================

import app as dashboard


# ============================================================
# 2.1. INSTRUMENTAÇÃO INTERNA DA CONSTRUÇÃO DA VISÃO GERAL
# ============================================================

def _registrar_memoria_etapa(etapa):
    """Registra RSS, USS e pico de RSS em uma etapa da Visão Geral."""
    memoria = _ler_memoria_linux()
    logger.info("VISÃO GERAL | %s | %s", etapa, _formatar_memoria(memoria))


# Preserva as funções originais do app.py e apenas adiciona medições.
_carregar_dados_dashboard_original = dashboard.carregar_dados_dashboard
_montar_visao_geral_original = dashboard._MONTADORES["visao_geral"]


def _carregar_dados_dashboard_instrumentado(uf, referencia):
    _registrar_memoria_etapa(
        f"antes de carregar_dados_dashboard | UF={uf} | ref={referencia}"
    )
    dados = _carregar_dados_dashboard_original(uf, referencia)
    _registrar_memoria_etapa(
        f"após carregar_dados_dashboard | UF={uf} | ref={referencia}"
    )
    return dados


def _montar_visao_geral_instrumentado(uf, referencia):
    _registrar_memoria_etapa(
        f"entrada de montar_visao_geral | UF={uf} | ref={referencia}"
    )
    layout = _montar_visao_geral_original(uf, referencia)
    _registrar_memoria_etapa(
        f"após criar_layout da Visão Geral | UF={uf} | ref={referencia}"
    )
    return layout


dashboard.carregar_dados_dashboard = _carregar_dados_dashboard_instrumentado
dashboard._MONTADORES["visao_geral"] = _montar_visao_geral_instrumentado


memoria_app = _ler_memoria_linux()

logger.info("APLICAÇÃO IMPORTADA E INICIALIZADA")
logger.info(_formatar_memoria(memoria_app))

if memoria_inicial["rss"] is not None and memoria_app["rss"] is not None:
    logger.info(
        "VARIAÇÃO NA INICIALIZAÇÃO: RSS=%+.1f MB",
        memoria_app["rss"] - memoria_inicial["rss"],
    )


# ============================================================
# 3. MONITORAMENTO DAS REQUISIÇÕES
# ============================================================

server = dashboard.server


@server.before_request
def registrar_inicio_requisicao():
    if request.path.startswith("/assets/"):
        return

    g.ram_inicio = _ler_memoria_linux()
    g.ram_tempo_inicio = time.perf_counter()

    if request.path == "/_dash-update-component":
        g.ram_contexto_dash = _resumir_requisicao_dash()

        contexto = g.ram_contexto_dash

        logger.info(
            "CALLBACK INÍCIO | página=%s | output=%s | alterados=%s | "
            "entradas=%s | %s",
            contexto.get("pagina") or "não identificada no payload",
            contexto.get("callback"),
            contexto.get("alterados"),
            contexto.get("entradas"),
            _formatar_memoria(g.ram_inicio),
        )


@server.after_request
def registrar_fim_requisicao(response):
    if not hasattr(g, "ram_inicio"):
        return response

    memoria_final = _ler_memoria_linux()
    tempo = time.perf_counter() - g.ram_tempo_inicio

    rss_inicio = g.ram_inicio["rss"]
    rss_final = memoria_final["rss"]

    variacao = (
        rss_final - rss_inicio
        if rss_inicio is not None and rss_final is not None
        else None
    )

    variacao_texto = (
        f"{variacao:+.1f} MB" if variacao is not None else "N/D"
    )

    if request.path == "/_dash-update-component":
        contexto = getattr(g, "ram_contexto_dash", {})

        logger.info(
            "CALLBACK FIM | página=%s | output=%s | status=%s | "
            "tempo=%.3fs | variação RSS=%s | %s",
            contexto.get("pagina") or "ver output/entradas acima",
            contexto.get("callback"),
            response.status_code,
            tempo,
            variacao_texto,
            _formatar_memoria(memoria_final),
        )
    else:
        logger.info(
            "REQUISIÇÃO | %s | status=%s | tempo=%.3fs | "
            "variação RSS=%s | %s",
            request.path,
            response.status_code,
            tempo,
            variacao_texto,
            _formatar_memoria(memoria_final),
        )

    return response


# ============================================================
# 4. EXECUÇÃO DO DASHBOARD
# ============================================================

if __name__ == "__main__":
    DEBUG = False
    PORT = int(os.environ.get("PORT", "8050"))
    HOST = os.environ.get("HOST", "127.0.0.1")

    logger.info("=" * 70)
    logger.info("DASHBOARD ENEM — DIAGNÓSTICO DE MEMÓRIA POR CALLBACK")
    logger.info("Endereço: http://%s:%s", HOST, PORT)
    logger.info("Arquivo de log: %s", ARQUIVO_LOG)
    logger.info("Debug: %s", DEBUG)
    logger.info("=" * 70)

    dashboard.app.run(
        debug=DEBUG,
        host=HOST,
        port=PORT,
        use_reloader=False,
    )
