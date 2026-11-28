"""Dashboard ENEM — aplicação preparada para produção."""

import gc
import os
from functools import lru_cache

# PyArrow lê esta variável na inicialização. Preserve valor fornecido pelo ambiente.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import psutil
from dash import Dash, Input, Output, dcc, html
from flask import g, request

from dash_utils.perf import LOG, configurar_logs, etapa, medir_callback

configurar_logs()

from dash_utils.data_loader import carregar_dados
from dash_utils.features_names import status_loader_otimizado
from pages.visao_geral import criar_layout
from pages.mapa_geral import criar_layout_mapa, registrar_callbacks_mapa
from pages.analise_municipal import criar_layout_analise, registrar_callbacks_analise
from pages.perfil_participantes import criar_layout_perfil, registrar_callbacks_perfil
from dash_utils.ufs import UFS, nome_uf

LOG.info("Configuração do loader: %s", status_loader_otimizado())

app = Dash(__name__, title="Dashboard ENEM", suppress_callback_exceptions=True)
server = app.server
_PROCESSO = psutil.Process(os.getpid())

# O deploy inicial possui somente os dados completos do Pará.
# Amplie esta variável apenas quando as bases e os shapefiles das demais UFs
# estiverem disponíveis no pacote de produção.
UFS_DISPONIVEIS = tuple(
    uf.strip().upper()
    for uf in os.environ.get("ENEM_UFS_DISPONIVEIS", "PA").split(",")
    if uf.strip()
)
if not UFS_DISPONIVEIS:
    raise RuntimeError("ENEM_UFS_DISPONIVEIS não pode ficar vazio.")
if any(uf not in UFS for uf in UFS_DISPONIVEIS):
    raise ValueError(f"UF inválida em ENEM_UFS_DISPONIVEIS: {UFS_DISPONIVEIS}")

UF_PADRAO = os.environ.get("ENEM_UF_PADRAO", UFS_DISPONIVEIS[0]).strip().upper()
if UF_PADRAO not in UFS_DISPONIVEIS:
    raise ValueError(
        f"UF padrão {UF_PADRAO} não está entre as UFs disponíveis: {UFS_DISPONIVEIS}"
    )

REF_PADRAO = os.environ.get("ENEM_REFERENCIA_PADRAO", "ESC").strip().upper()
if REF_PADRAO not in ("ESC", "PROVA"):
    REF_PADRAO = "ESC"


def _snapshot_memoria_mb():
    try:
        info = _PROCESSO.memory_full_info()
        return info.rss / 1024**2, getattr(info, "uss", 0) / 1024**2
    except Exception:
        return None


# Mantém monitoramento HTTP disponível para a primeira implantação.
# Desative com ENEM_HTTP_MEMORY_LOG=0 quando não for mais necessário.
if os.environ.get("ENEM_HTTP_MEMORY_LOG", "1") == "1":
    @server.before_request
    def _memoria_inicio_callback():
        if request.path.endswith("/_dash-update-component"):
            g._enem_memoria_inicio = _snapshot_memoria_mb()
            payload = request.get_json(silent=True) or {}
            g._enem_callback_output = str(payload.get("output", "callback"))[:180]

    @server.after_request
    def _memoria_fim_callback(response):
        if request.path.endswith("/_dash-update-component"):
            inicio = getattr(g, "_enem_memoria_inicio", None)
            fim = _snapshot_memoria_mb()
            nome = getattr(g, "_enem_callback_output", "callback")
            if fim is None:
                LOG.info(
                    "MEMORIA CALLBACK HTTP | output=%s | status=%s | indisponível",
                    nome, response.status_code,
                )
            elif inicio is None:
                LOG.info(
                    "MEMORIA CALLBACK HTTP | output=%s | status=%s | RSS=%.1f MB | USS=%.1f MB",
                    nome, response.status_code, fim[0], fim[1],
                )
            else:
                LOG.info(
                    "MEMORIA CALLBACK HTTP | output=%s | status=%s | "
                    "RSS=%.1f MB (%+.1f) | USS=%.1f MB (%+.1f)",
                    nome, response.status_code,
                    fim[0], fim[0] - inicio[0], fim[1], fim[1] - inicio[1],
                )
        return response


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
    """Mantém somente o último layout para limitar retenção de figuras."""
    with etapa(f"layout '{pagina}': construir", uf=uf, ref=referencia):
        return _MONTADORES[pagina](uf, referencia)


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div([
        dcc.Link("Visão Geral", href="/", style={"marginRight": "25px"}),
        dcc.Link("Mapas municipais", href="/mapas", style={"marginRight": "25px"}),
        dcc.Link("Análise municipal", href="/analise-municipal", style={"marginRight": "25px"}),
        dcc.Link("Perfil dos participantes", href="/perfil-participantes"),
    ], style={
        "maxWidth": "1900px", "margin": "0 auto", "padding": "18px 30px",
        "fontFamily": "Arial, sans-serif", "fontWeight": "600",
        "borderBottom": "1px solid #e2e8f0",
    }),
    html.Div([
        html.Div([
            html.Label(
                "Unidade da Federação",
                style={"display": "block", "fontWeight": "600", "marginBottom": "6px"},
            ),
            dcc.Dropdown(
                id="seletor-uf",
                options=[
                    {"label": f"{nome_uf(uf)} ({uf})", "value": uf}
                    for uf in UFS_DISPONIVEIS
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
                value=REF_PADRAO,
                clearable=False,
                searchable=False,
            ),
        ], id="referencia-global-container",
           style={"flex": "1", "minWidth": "280px", "maxWidth": "360px"}),
    ], style={
        "maxWidth": "1900px", "margin": "0 auto", "padding": "14px 30px 0",
        "fontFamily": "Arial, sans-serif", "display": "flex",
        "alignItems": "end", "gap": "16px", "flexWrap": "wrap",
    }),
    html.Div(id="conteudo-dashboard"),
])

_ULTIMA_COMBINACAO_LAYOUT = None


@app.callback(
    Output("conteudo-dashboard", "children"),
    Input("url", "pathname"),
    Input("seletor-referencia-territorial", "value"),
    Input("seletor-uf", "value"),
)
@medir_callback("atualizar_pagina")
def atualizar_pagina(pathname, referencia, uf):
    global _ULTIMA_COMBINACAO_LAYOUT

    pagina = _PAGINAS.get(pathname, "visao_geral")
    ref = referencia if referencia in ("ESC", "PROVA") else REF_PADRAO
    uf = uf or UF_PADRAO
    combinacao_atual = (uf, ref)

    if combinacao_atual != _ULTIMA_COMBINACAO_LAYOUT:
        if _ULTIMA_COMBINACAO_LAYOUT is not None:
            LOG.info("Limpando cache de layout: %s -> %s", _ULTIMA_COMBINACAO_LAYOUT, combinacao_atual)
            _layout_em_cache.cache_clear()
            gc.collect()
        _ULTIMA_COMBINACAO_LAYOUT = combinacao_atual

    hits_antes = _layout_em_cache.cache_info().hits
    layout = _layout_em_cache(pagina, uf, ref)
    if _layout_em_cache.cache_info().hits > hits_antes:
        LOG.info("Layout servido do cache | página=%s | UF=%s | ref=%s", pagina, uf, ref)
    LOG.info("Cache de layout: %s", _layout_em_cache.cache_info())
    return layout


registrar_callbacks_mapa(app, carregar_dados)
registrar_callbacks_analise(app, carregar_dados)
registrar_callbacks_perfil(app, carregar_dados)

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8050"))
    debug = os.environ.get("DASH_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
