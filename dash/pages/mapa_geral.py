#mapa_geral.py
import json
import threading
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html, no_update
from dash_utils.perf import etapa, medir_callback
from dash_utils.ufs import nome_uf

LIMITE_N = 100

# Simplificação das fronteiras (em graus; 0.002 ≈ 200 m). Reduz muito o tamanho do
# GeoJSON enviado ao navegador, com diferença visual desprezível na escala estadual.
# Use 0 para desativar e voltar à geometria original.
SIMPLIFICAR_GRAUS = 0.002

# {uf: {"features": {codigo_municipio: feature}}} — calculado uma vez por UF.
_GEOJSON_CACHE = {}
_GEOJSON_TRAVAS = {}
_GEOJSON_GUARDA = threading.Lock()


def _geojson_uf(uf, shape):
    """GeoJSON (EPSG:4326, simplificado) de uma UF, em cache.

    Só depende do shapefile da UF — não de ano, indicador ou dependência —, então
    não faz sentido recalculá-lo a cada filtro.
    """
    if uf in _GEOJSON_CACHE:
        return _GEOJSON_CACHE[uf]
    with _GEOJSON_GUARDA:
        trava = _GEOJSON_TRAVAS.setdefault(uf, threading.Lock())
    with trava:  # callbacks paralelos esperam o primeiro em vez de recalcular (MG: 2x ~3 s)
        if uf in _GEOJSON_CACHE:
            return _GEOJSON_CACHE[uf]
        return _construir_geojson_uf(uf, shape)


def _construir_geojson_uf(uf, shape):
    with etapa(f"geojson {uf}: construir (1x por UF)", tolerancia=SIMPLIFICAR_GRAUS):
        col_geom = shape.geometry.name
        g = shape[["CD_MUN", col_geom]].copy()
        if g.crs is not None and g.crs.to_epsg() != 4326:
            g = g.to_crs(epsg=4326)
        if SIMPLIFICAR_GRAUS:
            g.geometry = g.geometry.simplify(SIMPLIFICAR_GRAUS, preserve_topology=True)
        g["codigo_municipio"] = _codigo(g["CD_MUN"])
        colecao = json.loads(g[["codigo_municipio", col_geom]].to_json())
        feats = {f["properties"]["codigo_municipio"]: f for f in colecao["features"]}
    _GEOJSON_CACHE[uf] = feats
    return feats


def limpar_cache_geojson():
    _GEOJSON_CACHE.clear()


def _colecao(feats, codigos=None):
    """Monta um FeatureCollection a partir do cache (opcionalmente só alguns municípios)."""
    lista = feats.values() if codigos is None else [feats[c] for c in codigos if c in feats]
    return {"type": "FeatureCollection", "features": list(lista)}

INDICADORES = {
    "Participantes": ("contagem", None, 1998, 2025),
    "Redação": ("disciplina", "REDACAO", 1998, 2025),
    "Prova objetiva": ("disciplina", "OBJETIVA", 1998, 2008),
    "Ciências da Natureza": ("disciplina", "CN", 2009, 2025),
    "Ciências Humanas": ("disciplina", "CH", 2009, 2025),
    "Linguagens": ("disciplina", "LC", 2009, 2025),
    "Matemática": ("disciplina", "MT", 2009, 2025),
}

DEPENDENCIAS = {
    "Pública": ["FEDERAL", "ESTADUAL", "MUNICIPAL"],
    "Privada": ["PRIVADA"],
    "Pública + privada": ["FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA"],
    "Pública + privada + não informada": [
        "FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA", "NAO_INFORMADA"
    ],
    "Não informada": ["NAO_INFORMADA"],
}


def _codigo(serie):
    return (serie.astype("string").str.replace(r"\.0$", "", regex=True)
            .str.strip().str.zfill(7))


def obter_indicadores_disponiveis(ano):
    ano = int(ano)
    return [nome for nome, (_, _, ini, fim) in INDICADORES.items()
            if ini <= ano <= fim]


def _fmt(v):
    return "—" if pd.isna(v) else f"{v:,.0f}".replace(",", ".")


def _kpi(titulo, valor, ano):
    return html.Div([
        html.Div(titulo, style={"fontSize": "13px", "color": "#64748b"}),
        html.Div(_fmt(valor), style={
            "fontSize": "clamp(22px, 2vw, 34px)", "fontWeight": "700",
            "color": "#0f172a", "marginTop": "8px"
        }),
        html.Div(f"Ano {ano}", style={"fontSize": "11px", "color": "#94a3b8"})
    ], style={
        "background": "white", "border": "1px solid #e2e8f0",
        "borderRadius": "8px", "padding": "15px", "minWidth": "0"
    })


def calcular_kpis(painel, ano):
    df = painel.copy()
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df = df[df["ano"] == int(ano)]
    cols = ["n_participantes", "n_escola_federal", "n_escola_estadual",
            "n_escola_municipal", "n_escola_privada"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes para os KPIs: {missing}")
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    total = df["n_participantes"].sum()
    publica = df[["n_escola_federal", "n_escola_estadual",
                  "n_escola_municipal"]].sum().sum()
    privada = df["n_escola_privada"].sum()
    return {
        "total": total, "publica": publica, "privada": privada,
        "nao_informada": max(total - publica - privada, 0)
    }


def _kpis_componentes(painel, ano):
    k = calcular_kpis(painel, ano)
    return [
        _kpi("Total de participantes", k["total"], ano),
        _kpi("Escola pública", k["publica"], ano),
        _kpi("Escola privada", k["privada"], ano),
        _kpi("Dependência não informada", k["nao_informada"], ano),
    ]


def _sigla_uf_dados(dados):
    return dados["uf"]

def criar_layout_mapa(dados):
    anos = sorted(pd.to_numeric(dados["painel"]["ano"], errors="coerce")
                  .dropna().astype(int).unique().tolist())
    if not anos:
        raise ValueError("Não há anos disponíveis para a página de mapas.")
    ano = max(anos)
    indicadores = obter_indicadores_disponiveis(ano)

    return html.Div([
        html.Div([
            html.Div([
                html.Label("Referência territorial", style={"fontWeight": "600"}),
                html.Div("ESC ou PROVA", style={"color": "#64748b", "fontSize": "12px",
                                                "marginBottom": "18px"}),
                html.Label("Ano", style={"fontWeight": "600", "display": "block",
                                         "marginBottom": "6px"}),
                dcc.Dropdown(id="mapa-ano",
                    options=[{"label": str(a), "value": a} for a in anos],
                    value=ano, clearable=False,
                    style={"marginBottom": "16px"}),
                html.Label("Indicador", style={"fontWeight": "600", "display": "block",
                                               "marginBottom": "6px"}),
                dcc.Dropdown(id="mapa-indicador",
                    options=[{"label": x, "value": x} for x in indicadores],
                    value=indicadores[0], clearable=False,
                    style={"marginBottom": "16px"}),
                html.Label("Dependência administrativa",
                           style={"fontWeight": "600", "display": "block",
                                  "marginBottom": "6px"}),
                dcc.Dropdown(id="mapa-dependencia",
                    options=[{"label": x, "value": x} for x in DEPENDENCIAS],
                    value="Pública + privada + não informada", clearable=False),
                html.Hr(style={"margin": "22px 0"}),
                html.H4("Top 5 municípios", style={"margin": "0 0 4px"}),
                html.P("Maiores valores conforme os filtros selecionados.",
                       style={"fontSize": "12px", "color": "#64748b"}),
                dcc.Graph(id="mapa-top5", config={"displayModeBar": False},
                          style={"height": "370px"}),
            ], style={"background": "white", "border": "1px solid #e2e8f0",
                      "borderRadius": "8px", "padding": "16px", "minWidth": "250px"}),
            html.Div([
                html.Div(_kpis_componentes(dados["painel"], ano), id="mapa-kpis",
                    style={"display": "grid",
                           "gridTemplateColumns": "repeat(4, minmax(0, 1fr))",
                           "gap": "12px", "marginBottom": "14px"}),
                dcc.Loading(dcc.Graph(id="mapa-coropletico",
                    config={"displayModeBar": True, "responsive": True, "scrollZoom": False},
                    style={"height": "78vh", "minHeight": "680px"})),
            ], style={"minWidth": "0"}),
        ], style={"display": "grid",
                  "gridTemplateColumns": "minmax(260px, 310px) minmax(0, 1fr)",
                  "gap": "18px", "alignItems": "start"}),

        html.Div([
            html.H3("Análise estatística municipal",
                    style={"margin": "0 0 4px", "color": "#0f172a"}),
            html.P(
                "Distribuição, dispersão e cobertura dos resultados municipais "
                "para os filtros selecionados.",
                style={"margin": "0 0 14px", "fontSize": "13px",
                       "color": "#64748b"},
            ),
            html.Div(
                id="mapa-estatisticas",
                style={"display": "grid",
                       "gridTemplateColumns": "repeat(4, minmax(0, 1fr))",
                       "gap": "12px", "marginBottom": "14px"},
            ),
            html.Div([
                html.Div([
                    html.H4("Distribuição dos valores municipais",
                            style={"margin": "0 0 6px"}),
                    dcc.Graph(id="mapa-histograma",
                              config={"displayModeBar": False, "responsive": True},
                              style={"height": "360px"}),
                ], style={"background": "white", "border": "1px solid #e2e8f0",
                          "borderRadius": "8px", "padding": "14px", "minWidth": "0"}),
                html.Div([
                    html.H4("Dispersão dos resultados municipais",
                            style={"margin": "0 0 6px"}),
                    dcc.Graph(id="mapa-boxplot",
                              config={"displayModeBar": False, "responsive": True},
                              style={"height": "360px"}),
                ], style={"background": "white", "border": "1px solid #e2e8f0",
                          "borderRadius": "8px", "padding": "14px", "minWidth": "0"}),
            ], style={"display": "grid",
                      "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                      "gap": "14px"}),
        ], style={"marginTop": "24px", "padding": "18px",
                  "background": "#f1f5f9", "borderRadius": "10px"}),
    ], style={"width": "100%", "maxWidth": "1900px", "boxSizing": "border-box",
              "margin": "0 auto", "padding": "18px 22px 30px",
              "fontFamily": "Arial, sans-serif", "background": "#f8fafc",
              "minHeight": "calc(100vh - 100px)"})


def _valores_participantes(painel_ano, dependencia):
    df = painel_ano.copy()
    col = {"FEDERAL": "n_escola_federal", "ESTADUAL": "n_escola_estadual",
           "MUNICIPAL": "n_escola_municipal", "PRIVADA": "n_escola_privada"}
    for c in ["n_participantes", *col.values()]:
        if c not in df.columns:
            raise ValueError(f"Coluna ausente no painel: {c}")
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if dependencia == "Não informada":
        df["valor"] = (df["n_participantes"] - df[list(col.values())].sum(axis=1)).clip(lower=0)
    elif dependencia == "Pública + privada + não informada":
        df["valor"] = df["n_participantes"]
    else:
        df["valor"] = sum(df[col[g]] for g in DEPENDENCIAS[dependencia])
    df["n_valido"] = df["valor"]
    return df[["CO_MUNICIPIO_TERRITORIO", "valor", "n_valido"]]


def _valores_disciplina(grupo, ano, disciplina, dependencia):
    required = {"ano", "CO_MUNICIPIO_TERRITORIO", "tipo_grupo", "grupo",
                "disciplina", "media", "n_validos"}
    missing = required - set(grupo.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em desempenho por grupo: {sorted(missing)}")
    df = grupo.copy()
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["media"] = pd.to_numeric(df["media"], errors="coerce")
    df["n_validos"] = pd.to_numeric(df["n_validos"], errors="coerce")
    for c in ["tipo_grupo", "grupo", "disciplina"]:
        df[c] = df[c].astype(str).str.strip().str.upper()
    df = df[(df["ano"] == int(ano)) & (df["tipo_grupo"] == "ESCOLA")
            & (df["disciplina"] == disciplina)
            & df["grupo"].isin(DEPENDENCIAS[dependencia])
            & df["media"].notna() & df["n_validos"].gt(0)].copy()
    if df.empty:
        return pd.DataFrame(columns=["CO_MUNICIPIO_TERRITORIO", "valor", "n_valido"])
    df["ponderada"] = df["media"] * df["n_validos"]
    agg = df.groupby("CO_MUNICIPIO_TERRITORIO", as_index=False).agg(
        ponderada=("ponderada", "sum"), n_valido=("n_validos", "sum"))
    agg["valor"] = agg["ponderada"] / agg["n_valido"]
    return agg[["CO_MUNICIPIO_TERRITORIO", "valor", "n_valido"]]


def preparar_mapa(dados, ano, indicador, dependencia):
    painel = dados["painel"].copy()
    painel["ano"] = pd.to_numeric(painel["ano"], errors="coerce")
    painel_ano = painel[painel["ano"] == int(ano)].copy()
    if painel_ano.empty:
        raise ValueError(f"Não existem dados para o ano {ano}.")
    tipo, disciplina, _, _ = INDICADORES[indicador]
    if tipo == "contagem":
        valores = _valores_participantes(painel_ano, dependencia)
        unidade = "Participantes"
    else:
        if int(ano) < 2001:
            raise ValueError("A dependência administrativa não está disponível para este ano.")
        valores = _valores_disciplina(dados["grupo"], ano, disciplina, dependencia)
        unidade = "Média"

    valores["codigo_municipio"] = _codigo(valores["CO_MUNICIPIO_TERRITORIO"])
    # Só colunas de atributo: carregar a geometria aqui encarecia merge e cópias,
    # e os gráficos/estatísticas não a usam (o desenho usa o GeoJSON em cache).
    shape = pd.DataFrame(dados["shape"][["CD_MUN", "NM_MUN"]])
    shape["codigo_municipio"] = _codigo(shape["CD_MUN"])
    if valores["codigo_municipio"].duplicated().any():
        raise ValueError("Há códigos municipais duplicados nos valores do mapa.")
    mapa = shape.merge(
        valores[["codigo_municipio", "valor", "n_valido"]],
        on="codigo_municipio", how="left", validate="one_to_one")
    mapa["valor_mapa"] = mapa["valor"]
    mapa.loc[mapa["n_valido"].isna() | (mapa["n_valido"] <= LIMITE_N),
             "valor_mapa"] = float("nan")
    return mapa, unidade


def criar_figuras_mapa(dados, ano, indicador, dependencia, mapa=None, unidade=None):
    # Se o chamador já preparou o mapa, reaproveita (antes o merge era feito 2x).
    if mapa is None:
        mapa, unidade = preparar_mapa(dados, ano, indicador, dependencia)
    feats = _geojson_uf(_sigla_uf_dados(dados), dados["shape"])

    fig = go.Figure()

    # Camada territorial: todos os municípios, inclusive os sem dados.
    fig.add_trace(go.Choropleth(
        geojson=_colecao(feats, mapa["codigo_municipio"]),
        locations=mapa["codigo_municipio"],
        z=[0] * len(mapa),
        featureidkey="properties.codigo_municipio",
        colorscale=[
            [0, "rgba(255,255,255,0)"],
            [1, "rgba(255,255,255,0)"],
        ],
        showscale=False,
        marker_line_color="#777777",
        marker_line_width=0.7,
        hoverinfo="skip",
        showlegend=False,
    ))

    # Camada temática: somente municípios com N > 100.
    mapa_valido = mapa.dropna(subset=["valor_mapa"]).copy()

    if not mapa_valido.empty:
        fig.add_trace(go.Choropleth(
            geojson=_colecao(feats, mapa_valido["codigo_municipio"]),
            locations=mapa_valido["codigo_municipio"],
            z=mapa_valido["valor_mapa"],
            featureidkey="properties.codigo_municipio",
            colorscale="RdYlBu",
            marker_line_color="#777777",
            marker_line_width=0.7,
            colorbar={"title": unidade, "thickness": 18, "len": 0.8},
            customdata=mapa_valido[["NM_MUN", "n_valido"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                + unidade + ": %{z:,.2f}<br>"
                "N válido: %{customdata[1]:,.0f}<extra></extra>"
            ),
            showscale=True,
        ))
    else:
        fig.add_annotation(
            text="Não há municípios com N > 100 para este filtro.",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
        )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        template="plotly_white",
        autosize=True,
        height=850,
        margin=dict(l=0, r=0, t=60, b=0),
        title=f"{indicador} — {dependencia} — {nome_uf(_sigla_uf_dados(dados))} ({ano})",
    )

    top = (mapa[["NM_MUN", "valor_mapa"]].dropna()
           .nlargest(5, "valor_mapa").sort_values("valor_mapa"))
    if top.empty:
        ranking = go.Figure()
        ranking.add_annotation(text="Sem municípios com N > 100.",
                                x=.5, y=.5, xref="paper", yref="paper", showarrow=False)
        ranking.update_layout(template="plotly_white", height=350)
    else:
        top = top.copy()
        if unidade == "Participantes":
            top["rotulo_barra"] = top.apply(
                lambda row: f"{row['NM_MUN']}  |  {row['valor_mapa']:,.0f}".replace(",", "."),
                axis=1,
            )
        else:
            top["rotulo_barra"] = top.apply(
                lambda row: f"{row['NM_MUN']}  |  {row['valor_mapa']:.2f}",
                axis=1,
            )

        ranking = px.bar(
            top, x="valor_mapa", y="NM_MUN", orientation="h",
            text="rotulo_barra",
            labels={"valor_mapa": indicador, "NM_MUN": "Município"},
        )
        ranking.update_traces(
            marker_color="#1685d4",
            textposition="inside",
            insidetextanchor="middle",
            textfont={"color": "white", "size": 11},
            cliponaxis=False,
        )
        ranking.update_layout(
            template="plotly_white", height=370,
            margin=dict(l=5, r=10, t=10, b=35),
            yaxis={"title": "", "showticklabels": False},
            xaxis_title=indicador,
        )
    return fig, ranking



def calcular_estatisticas_municipais(mapa):
    """Estatísticas calculadas sobre municípios com N > 100."""
    df = mapa.dropna(subset=["valor_mapa"]).copy()
    valores = pd.to_numeric(df["valor_mapa"], errors="coerce").dropna()

    if valores.empty:
        return {
            "n_municipios": 0,
            "media": float("nan"),
            "cv": float("nan"),
            "amplitude": float("nan"),
        }

    media = float(valores.mean())
    desvio = float(valores.std(ddof=1)) if len(valores) > 1 else 0.0
    cv = (desvio / media * 100) if media != 0 else float("nan")

    return {
        "n_municipios": int(len(valores)),
        "media": media,
        "cv": float(cv),
        "amplitude": float(valores.max() - valores.min()),
    }


def _kpis_estatisticos(mapa, ano):
    stats = calcular_estatisticas_municipais(mapa)
    return [
        _kpi("Municípios com N > 100", stats["n_municipios"], ano),
        _kpi("Média municipal", stats["media"], ano),
        _kpi("Coeficiente de variação (%)", stats["cv"], ano),
        _kpi("Amplitude municipal", stats["amplitude"], ano),
    ]


def criar_figuras_estatisticas(mapa, indicador):
    df = mapa.dropna(subset=["valor_mapa"]).copy()
    hist = go.Figure()
    box = go.Figure()

    if df.empty:
        mensagem = "Não há municípios com N > 100 para os filtros selecionados."
        for figura in (hist, box):
            figura.add_annotation(
                text=mensagem, x=0.5, y=0.5,
                xref="paper", yref="paper", showarrow=False,
            )
            figura.update_layout(template="plotly_white")
        return hist, box

    hist.add_trace(go.Histogram(
        x=df["valor_mapa"],
        nbinsx=15,
        marker_color="#1685d4",
        opacity=0.85,
        hovertemplate="Valor: %{x}<br>Municípios: %{y}<extra></extra>",
    ))
    hist.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=45, r=15, t=15, b=45),
        xaxis_title=indicador,
        yaxis_title="Número de municípios",
        showlegend=False,
    )

    box.add_trace(go.Box(
        x=df["valor_mapa"],
        name=indicador,
        marker_color="#1685d4",
        boxmean=True,
        orientation="h",
        boxpoints="outliers",
        hovertemplate="Valor: %{x}<extra></extra>",
    ))
    box.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=35, r=15, t=15, b=45),
        xaxis_title=indicador,
        yaxis_title="",
        showlegend=False,
    )

    return hist, box


def registrar_callbacks_mapa(app, carregar_dados):
    @app.callback(
        Output("mapa-indicador", "options"),
        Output("mapa-indicador", "value"),
        Input("mapa-ano", "value"),
        State("mapa-indicador", "value"),
    )
    @medir_callback("mapa · atualizar_indicadores")
    def atualizar_indicadores(ano, atual):
        if ano is None:
            return [], None
        nomes = obter_indicadores_disponiveis(ano)
        valor = atual if atual in nomes else nomes[0]
        return [{"label": n, "value": n} for n in nomes], valor

    @app.callback(
        Output("mapa-kpis", "children"),
        Input("mapa-ano", "value"),
        State("seletor-referencia-territorial", "value"),
        State("seletor-uf", "value"),
        State("url", "pathname"),
    )
    @medir_callback("mapa · atualizar_kpis")
    def atualizar_kpis(ano, referencia, uf, pathname):
        if pathname != "/mapas" or ano is None:
            return no_update
        ref = referencia if referencia in ("ESC", "PROVA") else "ESC"
        dados = carregar_dados(uf, referencia=ref)
        return _kpis_componentes(dados["painel"], ano)

    @app.callback(
        Output("mapa-coropletico", "figure"),
        Output("mapa-top5", "figure"),
        Output("mapa-estatisticas", "children"),
        Output("mapa-histograma", "figure"),
        Output("mapa-boxplot", "figure"),
        Input("mapa-ano", "value"),
        Input("mapa-indicador", "value"),
        Input("mapa-dependencia", "value"),
        State("seletor-referencia-territorial", "value"),
        State("seletor-uf", "value"),
        State("url", "pathname"),
    )
    @medir_callback("mapa · atualizar_mapa")
    def atualizar_mapa(ano, indicador, dependencia, referencia, uf, pathname):
        if pathname != "/mapas" or any(v is None for v in (ano, indicador, dependencia)):
            return no_update, no_update, no_update, no_update, no_update
        ref = referencia if referencia in ("ESC", "PROVA") else "ESC"
        dados = carregar_dados(uf, referencia=ref)
        dados["uf"] = uf
        try:
            with etapa("mapa: preparar valores + merge", uf=uf, ano=ano, indicador=indicador):
                mapa, unidade = preparar_mapa(dados, ano, indicador, dependencia)
            with etapa("mapa: montar figuras (mapa + top 5)"):
                mapa_fig, top_fig = criar_figuras_mapa(
                    dados, ano, indicador, dependencia, mapa=mapa, unidade=unidade)
            with etapa("mapa: estatísticas, histograma, boxplot"):
                stats_kpis = _kpis_estatisticos(mapa, ano)
                hist_fig, box_fig = criar_figuras_estatisticas(mapa, indicador)
            return mapa_fig, top_fig, stats_kpis, hist_fig, box_fig
        except ValueError as exc:
            fig = go.Figure()
            fig.add_annotation(text=str(exc), x=.5, y=.5,
                               xref="paper", yref="paper", showarrow=False)
            fig.update_layout(template="plotly_white", height=500)
            return fig, fig, [], fig, fig
