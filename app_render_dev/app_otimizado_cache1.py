#app_otimizado_cache1.py
import os
import gc
import psutil

# Definir o Memory Pool antes de importar qualquer módulo que possa carregar PyArrow.
os.environ["ARROW_DEFAULT_MEMORY_POOL"] = os.environ.get("ENEM_ARROW_MEMORY_POOL", "system")

from functools import lru_cache

from dash import Dash, Input, Output, dcc, html

from dash_utils.perf import LOG, configurar_logs, etapa, medir_callback

configurar_logs()  # logs do projeto no terminal (ENEM_PERF=0 silencia)

from dash_utils.data_loader_otimizado import carregar_dados, status_cache_dados
from dash_utils.features_names_otimizado import status_loader_otimizado
LOG.info("Configuração Arrow: %s", status_loader_otimizado())
from pages.visao_geral import criar_layout
from pages.mapa_geral import criar_layout_mapa, registrar_callbacks_mapa
from pages.analise_municipal import criar_layout_analise, registrar_callbacks_analise
from pages.perfil_participantes import criar_layout_perfil, registrar_callbacks_perfil
from dash_utils.ufs import UFS, nome_uf

app = Dash(__name__, title="Dashboard ENEM — cache de layout 1",
           suppress_callback_exceptions=True)

# Mede a memória no limite HTTP do Dash: depois que o callback foi executado
# e a resposta foi produzida pelo Flask. Não altera os decorators existentes.
from flask import g, request


def _snapshot_memoria_mb():
    try:
        info = _PROCESSO.memory_full_info()
        return info.rss / 1024**2, getattr(info, "uss", 0) / 1024**2
    except Exception:
        return None


@app.server.before_request
def _memoria_inicio_callback():
    if request.path.endswith("/_dash-update-component"):
        g._enem_memoria_inicio = _snapshot_memoria_mb()
        payload = request.get_json(silent=True) or {}
        g._enem_callback_output = str(payload.get("output", "callback"))[:180]


@app.server.after_request
def _memoria_fim_callback(response):
    if request.path.endswith("/_dash-update-component"):
        inicio = getattr(g, "_enem_memoria_inicio", None)
        fim = _snapshot_memoria_mb()
        nome = getattr(g, "_enem_callback_output", "callback")
        if fim is None:
            LOG.info("MEMORIA CALLBACK HTTP | output=%s | status=%s | indisponível",
                     nome, response.status_code)
        elif inicio is None:
            LOG.info("MEMORIA CALLBACK HTTP | output=%s | status=%s | RSS=%.1f MB | USS=%.1f MB",
                     nome, response.status_code, fim[0], fim[1])
        else:
            LOG.info(
                "MEMORIA CALLBACK HTTP | output=%s | status=%s | "
                "RSS=%.1f MB (%+.1f) | USS=%.1f MB (%+.1f)",
                nome, response.status_code,
                fim[0], fim[0] - inicio[0], fim[1], fim[1] - inicio[1],
            )
    return response


UF_PADRAO = os.environ.get("ENEM_UF_PADRAO", "PA").strip().upper()

def carregar_dados_dashboard(uf, referencia):
    dados = carregar_dados(uf, referencia=referencia)
    dados["uf"] = uf
    return dados


def montar_visao_geral(uf, referencia):
    return criar_layout(carregar_dados_dashboard(uf, referencia))


def montar_pagina_mapa(uf, referencia):
    return criar_layout_mapa(carregar_dados_dashboard(uf, referencia))


def montar_pagina_analise(uf, referencia):
    return criar_layout_analise(carregar_dados_dashboard(uf, referencia))


def montar_pagina_perfil(uf, referencia):
    return criar_layout_perfil(carregar_dados_dashboard(uf, referencia))


_MONTADORES = {
    "visao_geral": montar_visao_geral,
    "mapas": montar_pagina_mapa,
    "analise": montar_pagina_analise,
    "perfil": montar_pagina_perfil,
}



_PAGINAS = {
    "/mapas": "mapas",
    "/analise-municipal": "analise",
    "/perfil-participantes": "perfil",
}




@lru_cache(maxsize=1)
def _layout_em_cache(pagina, uf, referencia):
    """Mantém somente o layout mais recentemente utilizado.

    Ao navegar para outra página, o layout anterior sai do cache LRU.
    A limpeza explícita na troca de UF/referência também é mantida.
    """
    with etapa(f"layout '{pagina}': construir (cache miss)", uf=uf, ref=referencia):
        return _MONTADORES[pagina](uf, referencia)


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div([
        dcc.Link("Visão Geral", href="/", style={"marginRight": "25px"}),
        dcc.Link("Mapas municipais", href="/mapas",
                 style={"marginRight": "25px"}),
        dcc.Link("Análise municipal", href="/analise-municipal", style={"marginRight": "25px"}),
        dcc.Link("Perfil dos participantes", href="/perfil-participantes"),
    ], style={"maxWidth": "1900px", "margin": "0 auto",
              "padding": "18px 30px", "fontFamily": "Arial, sans-serif",
              "fontWeight": "600", "borderBottom": "1px solid #e2e8f0"}),
    html.Div([
        html.Div([
            html.Label(
                "Unidade da Federação",
                style={"display": "block", "fontWeight": "600", "marginBottom": "6px"},
            ),
            dcc.Dropdown(
                id="seletor-uf",
                options=[
                    {"label": f"{nome} ({sigla})", "value": sigla}
                    for sigla, nome in sorted(UFS.items(), key=lambda item: item[1])
                ],
                value=UF_PADRAO,
                clearable=False,
                searchable=True,
            ),
        ], style={"flex": "1", "minWidth": "280px", "maxWidth": "360px"}),
        html.Div([
            html.Label(
                "Referência territorial",
                style={"display": "block", "fontWeight": "600", "marginBottom": "6px"},
            ),
            dcc.Dropdown(
                id="seletor-referencia-territorial",
                options=[
                    {"label": "Escola (ESC)", "value": "ESC"},
                    {"label": "Local de prova (PROVA)", "value": "PROVA"},
                ],
                value="ESC",
                clearable=False,
                searchable=False,
            ),
        ], id="referencia-global-container",
           style={"flex": "1", "minWidth": "280px", "maxWidth": "360px"}),
    ], style={
        "maxWidth": "1900px",
        "margin": "0 auto",
        "padding": "14px 30px 0",
        "fontFamily": "Arial, sans-serif",
        "display": "flex",
        "alignItems": "end",
        "gap": "16px",
        "flexWrap": "wrap",
    }),
    html.Div(id="conteudo-dashboard"),
])


_ULTIMA_COMBINACAO_LAYOUT = None
_PROCESSO = psutil.Process(os.getpid())


def _log_memoria_layout(evento):
    """Registra RSS/USS nos limites do cache de layouts."""
    try:
        memoria = _PROCESSO.memory_full_info()
        LOG.info(
            "MEMORIA LAYOUT | %s | RSS=%.1f MB | USS=%.1f MB | cache=%s",
            evento,
            memoria.rss / 1024**2,
            getattr(memoria, "uss", 0) / 1024**2,
            _layout_em_cache.cache_info(),
        )
    except Exception as exc:
        LOG.warning("Não foi possível medir memória do layout: %s", exc)


@app.callback(
    Output("conteudo-dashboard", "children"),
    Input("url", "pathname"),
    Input("seletor-referencia-territorial", "value"),
    Input("seletor-uf", "value"),
)
@medir_callback("atualizar_pagina (reconstrói a página)")
def atualizar_pagina(pathname, referencia, uf):
    global _ULTIMA_COMBINACAO_LAYOUT

    pagina = _PAGINAS.get(pathname, "visao_geral")
    ref = referencia if referencia in ("ESC", "PROVA") else "ESC"
    uf = uf or UF_PADRAO
    combinacao_atual = (uf, ref)

    # O cache de dados (ENEM_CACHE_MAX_ENTRIES) não controla este outro cache.
    # Ao mudar UF ou referência, descarta layouts/figuras da combinação anterior.
    if (
        _ULTIMA_COMBINACAO_LAYOUT is not None
        and combinacao_atual != _ULTIMA_COMBINACAO_LAYOUT
    ):
        _log_memoria_layout("antes de limpar layouts da combinação anterior")
        _layout_em_cache.cache_clear()
        coletados = gc.collect()
        LOG.info(
            "CACHE LAYOUT LIMPO | anterior=%s | atual=%s | objetos_coletados=%s",
            _ULTIMA_COMBINACAO_LAYOUT,
            combinacao_atual,
            coletados,
        )
        _log_memoria_layout("depois de limpar layouts + gc")

    _ULTIMA_COMBINACAO_LAYOUT = combinacao_atual

    antes = _layout_em_cache.cache_info().hits
    layout = _layout_em_cache(pagina, uf, ref)
    if _layout_em_cache.cache_info().hits > antes:
        LOG.info("    · layout '%s' veio do cache (UF=%s ref=%s)", pagina, uf, ref)

    _log_memoria_layout(f"fim atualizar_pagina | página={pagina} | UF={uf} | ref={ref}")
    return layout


registrar_callbacks_mapa(app, carregar_dados)
registrar_callbacks_analise(app, carregar_dados)
registrar_callbacks_perfil(app, carregar_dados)

server = app.server

# if __name__ == "__main__":
#     DEBUG = True
#     # No modo debug o Flask sobe dois processos; o banner sai só no que atende as requisições.
#     if not DEBUG or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
#         LOG.info("=" * 60)
#         LOG.info("Dashboard ENEM em http://127.0.0.1:8050  (debug=%s)", DEBUG)
#         LOG.info("UF padrão: %s | logs: ENEM_PERF=0 silencia, =2 mostra argumentos", UF_PADRAO)
#         LOG.info("=" * 60)
#         if os.environ.get("ENEM_PREAQUECER") == "1":
#             from pages.mapa_geral import _geojson_uf
#             with etapa(f"pré-aquecer {UF_PADRAO} (dados + geojson)"):
#                 _d = carregar_dados(UF_PADRAO, referencia="ESC")
#                 _geojson_uf(UF_PADRAO, _d["shape"])
#     app.run(debug=DEBUG, host="127.0.0.1", port=8050)


if __name__ == "__main__":
    DEBUG = os.environ.get("DASH_DEBUG", "0") == "1"
    PORT = int(os.environ.get("PORT", "8050"))
    HOST = os.environ.get("HOST", "127.0.0.1")

    if not DEBUG or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        LOG.info("=" * 60)
        LOG.info("Dashboard ENEM em http://%s:%s (debug=%s)", HOST, PORT, DEBUG)
        LOG.info("UF padrão: %s | logs: ENEM_PERF=0 silencia, =2 mostra argumentos", UF_PADRAO)
        LOG.info("=" * 60)

        if os.environ.get("ENEM_PREAQUECER") == "1":
            from pages.mapa_geral import _geojson_uf
            with etapa(f"pré-aquecer {UF_PADRAO} (dados + geojson)"):
                _d = carregar_dados(UF_PADRAO, referencia="ESC")
                _geojson_uf(UF_PADRAO, _d["shape"])

    app.run(debug=DEBUG, host=HOST, port=PORT)