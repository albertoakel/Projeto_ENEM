#app.py
import os
from functools import lru_cache

from dash import Dash, Input, Output, dcc, html

from dash_utils.perf import LOG, configurar_logs, etapa, medir_callback

configurar_logs()  # logs do projeto no terminal (ENEM_PERF=0 silencia)

from dash_utils.data_loader import carregar_dados, status_cache_dados
from pages.visao_geral import criar_layout
from pages.mapa_geral import criar_layout_mapa, registrar_callbacks_mapa
from pages.analise_municipal import criar_layout_analise, registrar_callbacks_analise
from pages.perfil_participantes import criar_layout_perfil, registrar_callbacks_perfil
from dash_utils.ufs import UFS, nome_uf

app = Dash(__name__, title="Dashboard ENEM",
           suppress_callback_exceptions=True)


UF_PADRAO = "PA"

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




@lru_cache(maxsize=16)
def _layout_em_cache(pagina, uf, referencia):
    """O layout de cada página só depende de (página, UF, referência).

    Antes ele era reconstruído do zero (incluindo todos os gráficos da Visão Geral)
    a cada troca de página ou de dropdown, mesmo voltando a uma combinação já vista.
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


@app.callback(
    Output("conteudo-dashboard", "children"),
    Input("url", "pathname"),
    Input("seletor-referencia-territorial", "value"),
    Input("seletor-uf", "value"),
)
@medir_callback("atualizar_pagina (reconstrói a página)")
def atualizar_pagina(pathname, referencia, uf):
    pagina = _PAGINAS.get(pathname, "visao_geral")
    ref = referencia if referencia in ("ESC", "PROVA") else "ESC"
    uf = uf or UF_PADRAO
    antes = _layout_em_cache.cache_info().hits
    layout = _layout_em_cache(pagina, uf, ref)
    if _layout_em_cache.cache_info().hits > antes:
        LOG.info("    · layout '%s' veio do cache (UF=%s ref=%s)", pagina, uf, ref)
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