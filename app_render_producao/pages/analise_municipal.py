#analise_municipal.py
"""Página de análise individual e comparativa dos municípios do ENEM."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from dash import Input, Output, State, dcc, html, no_update
from dash_utils.ufs import nome_uf
from dash_utils.perf import etapa, medir_callback


DEPENDENCIAS = {
    "Todas": None,
    "Pública": ["FEDERAL", "ESTADUAL", "MUNICIPAL"],
    "Privada": ["PRIVADA"],
    "Pública + privada": ["FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA"],
    "Pública + privada + não informada": [
        "FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA", "NAO_INFORMADA"
    ],
    "Não informada": ["NAO_INFORMADA"],
}

DISCIPLINAS = {
    "Redação": "REDACAO",
    "Ciências da Natureza": "CN",
    "Ciências Humanas": "CH",
    "Linguagens": "LC",
    "Matemática": "MT",
}

AREAS = list(DISCIPLINAS.keys())
LIMITE_N = 100

# Limite mínimo de participantes para calcular as medianas dos quadrantes.
# Altere este valor se desejar outro critério de cobertura (ex.: 50, 100 ou 200).
# Municípios abaixo do limite continuam visíveis no gráfico, mas NÃO definem
# as linhas de corte dos quadrantes.
LIMITE_N_QUADRANTES = 100


# Paleta editável: quatro cores principais e suas quatro variantes claras.
# A ordem acompanha município principal e municípios de comparação.
CORES_MUNICIPIOS = {
    "principais": ["#d7191c", "#fdae61", "#2c7bb6", "#1a9641"],
    "variantes": ["#f28e91", "#fdd49e", "#91bfdb", "#a6dba0"],
}


def _codigo(serie):
    return (
        serie.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(7)
    )


def _card(titulo, valor, subtitulo=""):
    if pd.isna(valor):
        exibicao = "—"
    elif isinstance(valor, (int, np.integer)):
        exibicao = f"{valor:,}".replace(",", ".")
    elif isinstance(valor, (float, np.floating)):
        exibicao = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        exibicao = str(valor)

    return html.Div(
        [
            html.Div(titulo, style={"fontSize": "12px", "color": "#64748b"}),
            html.Div(
                exibicao,
                style={
                    "fontSize": "26px",
                    "fontWeight": "700",
                    "color": "#0f172a",
                    "marginTop": "7px",
                },
            ),
            html.Div(subtitulo, style={"fontSize": "10px", "color": "#94a3b8"}),
        ],
        style={
            "background": "white",
            "border": "1px solid #e2e8f0",
            "borderRadius": "8px",
            "padding": "14px",
            "minWidth": "0",
        },
    )


def _painel_municipios(painel):
    df = painel.copy()
    if "CO_MUNICIPIO_TERRITORIO" not in df or "NO_MUNICIPIO_TERRITORIO" not in df:
        raise ValueError(
            "O painel precisa conter CO_MUNICIPIO_TERRITORIO e "
            "NO_MUNICIPIO_TERRITORIO."
        )
    df["codigo"] = _codigo(df["CO_MUNICIPIO_TERRITORIO"])
    nomes = (
        df[["codigo", "NO_MUNICIPIO_TERRITORIO"]]
        .dropna()
        .drop_duplicates("codigo")
        .sort_values("NO_MUNICIPIO_TERRITORIO")
    )
    return nomes


def _sigla_uf_dados(dados):
    return dados["uf"]

def criar_layout_analise(dados):
    """Constrói a página; recebe o mesmo dicionário retornado por carregar_dados()."""
    painel = dados["painel"]
    municipios = _painel_municipios(painel)
    opcoes = [
        {"label": nome, "value": codigo}
        for codigo, nome in zip(
            municipios["codigo"], municipios["NO_MUNICIPIO_TERRITORIO"]
        )
    ]
    if not opcoes:
        raise ValueError("Não foram encontrados municípios no painel.")

    anos = sorted(
        pd.to_numeric(painel["ano"], errors="coerce").dropna().astype(int).unique()
    )
    ano_final = int(max(anos))

    return html.Div(
        [
            html.H2(f"Análise individual dos municípios — ENEM em {nome_uf(_sigla_uf_dados(dados))}"),
            html.P(
                "Evolução histórica, comparação municipal, dispersão e tendências.",
                style={"color": "#64748b"},
            ),

            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Município principal", style={"fontWeight": "600"}),
                            dcc.Dropdown(
                                id="analise-municipio-principal",
                                options=opcoes,
                                value=opcoes[min(18, len(opcoes) - 1)]["value"],
                                clearable=False,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label("Municípios para comparação", style={"fontWeight": "600"}),
                            dcc.Dropdown(
                                id="analise-municipios-comparacao",
                                options=opcoes,
                                value=[],
                                multi=True,
                                placeholder="Selecione até quatro municípios",
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label("Dependência administrativa", style={"fontWeight": "600"}),
                            dcc.Dropdown(
                                id="analise-dependencia",
                                options=[{"label": x, "value": x} for x in DEPENDENCIAS],
                                value="Todas",
                                clearable=False,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label("Indicador de desempenho", style={"fontWeight": "600"}),
                            dcc.Dropdown(
                                id="analise-disciplina",
                                options=[{"label": x, "value": x} for x in AREAS],
                                value="Redação",
                                clearable=False,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label("Ano de referência", style={"fontWeight": "600"}),
                            dcc.Dropdown(
                                id="analise-ano",
                                options=[{"label": str(a), "value": a} for a in anos],
 #                               value=ano_final,
                                value=2020,
                                clearable=False,
                            ),
                        ]
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                    "gap": "14px",
                    "background": "white",
                    "border": "1px solid #e2e8f0",
                    "borderRadius": "8px",
                    "padding": "16px",
                    "marginBottom": "18px",
                },
            ),

            html.Div(
                id="analise-kpis",
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, minmax(0, 1fr))",
                    "gap": "12px",
                    "marginBottom": "22px",
                },
            ),

            html.H3("1. Evolução histórica"),
            html.Div(
                [
                    dcc.Graph(id="analise-evolucao-participantes", config={"responsive": True}),
                    dcc.Graph(id="analise-evolucao-desempenho", config={"responsive": True}),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                    "gap": "14px",
                },
            ),

            html.Div(id="analise-tendencia-redacao"),

            html.H3("2. Comparação entre municípios", style={"marginTop": "26px"}),
            dcc.Graph(id="analise-comparacao", config={"responsive": True}),

            html.H3("3. Relação entre volume de notas e desempenho", style={"marginTop": "26px"}),
            html.P(
                 "Cada ponto representa uma dependência administrativa de um município no ano selecionado. "
                 "O eixo horizontal mostra o número de notas válidas e o vertical a média da avaliação selecionada. "
                 "Círculos representam a rede pública e quadrados a privada; "
                 "a comparação apresenta exclusivamente as redes pública e privada, "
                 "independentemente do filtro de dependência administrativa selecionado. "
                 "As linhas tracejadas indicam as medianas usadas como referência para os quadrantes.",
                style={"color": "#64748b", "fontSize": "13px"},
            ),
            dcc.Graph(id="analise-dispersao", config={"responsive": True}),
            html.Div(id="analise-correlacao", style={"marginBottom": "18px"}),

            html.Div(
                "Nota metodológica: médias calculadas de forma ponderada pelo número "
                "de notas válidas. As tendências são descritivas e não implicam causalidade. "
                "Anos sem disponibilidade de determinada avaliação não são interpolados.",
                style={
                    "fontSize": "11px",
                    "color": "#64748b",
                    "borderTop": "1px solid #e2e8f0",
                    "paddingTop": "12px",
                    "marginTop": "18px",
                },
            ),
        ],
        style={
            "width": "100%",
            "maxWidth": "1900px",
            "margin": "0 auto",
            "padding": "22px",
            "boxSizing": "border-box",
            "background": "#f8fafc",
        },
    )


def _nomes_municipios(painel):
    nomes = _painel_municipios(painel)
    return dict(zip(nomes["codigo"], nomes["NO_MUNICIPIO_TERRITORIO"]))


def _filtrar_grupo(grupo, dependencia):
    df = grupo.copy()
    for col in ["tipo_grupo", "grupo", "disciplina"]:
        df[col] = df[col].astype(str).str.strip().str.upper()

    df = df[df["tipo_grupo"] == "ESCOLA"]
    grupos = DEPENDENCIAS[dependencia]
    if grupos is not None:
        df = df[df["grupo"].isin(grupos)]
    return df


def _serie_desempenho(grupo, codigos, dependencia, disciplina=None):
    df = _filtrar_grupo(grupo, dependencia)
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["media"] = pd.to_numeric(df["media"], errors="coerce")
    df["n_validos"] = pd.to_numeric(df["n_validos"], errors="coerce")
    df["codigo"] = _codigo(df["CO_MUNICIPIO_TERRITORIO"])

    if disciplina is not None:
        df = df[df["disciplina"] == disciplina]

    df = df[
        df["codigo"].isin(codigos)
        & df["media"].notna()
        & df["n_validos"].gt(0)
    ].copy()

    if df.empty:
        return pd.DataFrame(columns=["codigo", "ano", "disciplina", "media", "n_validos"])

    df["soma_ponderada"] = df["media"] * df["n_validos"]
    agrupado = (
        df.groupby(["codigo", "ano", "disciplina"], as_index=False)
        .agg(
            soma_ponderada=("soma_ponderada", "sum"),
            n_validos=("n_validos", "sum"),
        )
    )
    agrupado["media"] = agrupado["soma_ponderada"] / agrupado["n_validos"]

    # Redação: escala 0–100 até 2008 e 0–1000 a partir de 2009.
    # A normalização ocorre somente na camada analítica do dashboard.
    mask_pre_2009 = agrupado["disciplina"].eq("REDACAO") & agrupado["ano"].le(2008)
    agrupado.loc[mask_pre_2009, "media"] *= 10

    return agrupado[["codigo", "ano", "disciplina", "media", "n_validos"]]

def _serie_participantes(painel, codigos, dependencia):
    df = painel.copy()
    df["codigo"] = _codigo(df["CO_MUNICIPIO_TERRITORIO"])
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")

    colunas = {
        "FEDERAL": "n_escola_federal",
        "ESTADUAL": "n_escola_estadual",
        "MUNICIPAL": "n_escola_municipal",
        "PRIVADA": "n_escola_privada",
    }

    df["n_participantes"] = pd.to_numeric(
        df["n_participantes"], errors="coerce"
    ).fillna(0)

    if dependencia == "Todas":
        df["valor"] = df["n_participantes"]

    else:
        selecionadas = DEPENDENCIAS[dependencia]
        valores = []

        for grupo in selecionadas:
            if grupo == "NAO_INFORMADA":
                publica_privada = [
                    "n_escola_federal",
                    "n_escola_estadual",
                    "n_escola_municipal",
                    "n_escola_privada",
                ]

                for coluna in publica_privada:
                    df[coluna] = pd.to_numeric(
                        df[coluna], errors="coerce"
                    ).fillna(0)

                residual = (
                    df["n_participantes"]
                    - df[publica_privada].sum(axis=1)
                )
                valores.append(residual)

            else:
                coluna = colunas[grupo]

                if coluna not in df.columns:
                    raise ValueError(
                        f"Coluna de dependência ausente: {coluna}"
                    )

                df[coluna] = pd.to_numeric(
                    df[coluna], errors="coerce"
                ).fillna(0)

                valores.append(df[coluna])

        df["valor"] = sum(valores)

    df = df[df["codigo"].isin(codigos)]

    return (
        df.groupby(["codigo", "ano"], as_index=False)["valor"]
        .sum()
        .rename(columns={"valor": "participantes"})
    )





def _regressao(x, y):
    """Retorna valores ajustados, inclinação anual e R²; ignora séries insuficientes."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    validos = np.isfinite(x) & np.isfinite(y)
    x, y = x[validos], y[validos]
    if len(x) < 3 or len(np.unique(x)) < 2:
        return None

    coef = np.polyfit(x, y, 1)
    ajustados = np.polyval(coef, x)
    ss_res = float(np.sum((y - ajustados) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return ajustados, float(coef[0]), float(r2)


class _ResultadoOLSLeve:
    """Resultado mínimo compatível com os atributos usados na página."""

    def __init__(self, params, pvalues, rsquared):
        self.params = params
        self.pvalues = pvalues
        self.rsquared = float(rsquared)

    def predict(self, exog):
        if isinstance(exog, pd.DataFrame):
            matriz = exog.loc[:, self.params.index].to_numpy(dtype=float)
        else:
            matriz = np.asarray(exog, dtype=float)
        return matriz @ self.params.to_numpy(dtype=float)


def _ajustar_ols_leve(endog, exog):
    """Ajusta OLS com NumPy e calcula p-valores t sem importar statsmodels."""
    from scipy.special import stdtr

    if not isinstance(exog, pd.DataFrame):
        raise TypeError("exog deve ser um DataFrame para preservar os nomes dos coeficientes")

    matriz = exog.to_numpy(dtype=float)
    y = np.asarray(endog, dtype=float).reshape(-1)
    validos = np.isfinite(y) & np.isfinite(matriz).all(axis=1)
    matriz = matriz[validos]
    y = y[validos]
    nomes = list(exog.columns)

    if len(y) == 0:
        raise ValueError("Não há observações válidas para ajustar o modelo OLS")

    # A pseudoinversa via SVD acompanha a solução de mínimos quadrados
    # usada pelo OLS e evita formar explicitamente X'X.
    pinv = np.linalg.pinv(matriz, rcond=1e-15)
    beta = pinv @ y
    ajustados = matriz @ beta
    residuos = y - ajustados
    rank = int(np.linalg.matrix_rank(matriz))
    graus_liberdade = len(y) - rank

    ss_res = float(residuos @ residuos)
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

    if graus_liberdade > 0:
        mse = ss_res / graus_liberdade
        cov = (pinv @ pinv.T) * mse
        erros_padrao = np.sqrt(np.clip(np.diag(cov), 0.0, None))
        t_values = np.divide(
            beta, erros_padrao,
            out=np.full(beta.shape, np.nan, dtype=float),
            where=erros_padrao > 0,
        )
        p_values = 2.0 * stdtr(graus_liberdade, -np.abs(t_values))
        p_values[(erros_padrao == 0) & (beta != 0)] = 0.0
    else:
        p_values = np.full(beta.shape, np.nan, dtype=float)

    return _ResultadoOLSLeve(
        params=pd.Series(beta, index=nomes, dtype=float),
        pvalues=pd.Series(p_values, index=nomes, dtype=float),
        rsquared=r2,
    )


def _regressao_periodo(parte):
    """Regressão linear simples com NumPy/SciPy, sem dependência de statsmodels."""
    parte = parte.dropna(subset=["ano", "media"]).sort_values("ano")
    if len(parte) < 3 or parte["ano"].nunique() < 2:
        return None

    anos = parte["ano"].astype(float)
    # Centralizar o ano melhora o condicionamento numérico; a inclinação
    # anual e os valores ajustados permanecem os mesmos.
    X = pd.DataFrame({
        "const": 1.0,
        "ano": anos - float(anos.min()),
    }, index=parte.index)
    modelo = _ajustar_ols_leve(parte["media"].astype(float), X)
    return modelo, modelo.predict(X)


def _modelo_redacao_dummy(parte):
    """OLS: nota ~ ano + pos_2009, sem importar statsmodels."""
    df = parte.dropna(subset=["ano", "media"]).copy()
    if len(df) < 4 or df["ano"].nunique() < 3 or not df["ano"].ge(2009).any():
        return None

    anos = df["ano"].astype(float)
    X = pd.DataFrame({
        "const": 1.0,
        "ano": anos - 2000.0,
        "pos_2009": df["ano"].ge(2009).astype(int),
    }, index=df.index)
    modelo = _ajustar_ols_leve(df["media"].astype(float), X)
    df["ajustada_dummy"] = modelo.predict(X)
    return modelo, df


def _fmt(valor, casas=3):
    return "—" if pd.isna(valor) else f"{valor:.{casas}f}".replace(".", ",")


def _fmt_p(valor):
    if pd.isna(valor):
        return "—"
    if valor < 0.001:
        return "< 0,001"
    return _fmt(valor, 3)


def _resumo_tendencias_disciplina(df, nomes, disciplina):
    """Tabela estatística para qualquer disciplina, respeitando sua cobertura temporal."""
    linhas = []
    reda = disciplina == "Redação"

    for codigo, parte in df.groupby("codigo"):
        nome = nomes.get(codigo, codigo)
        pos = _regressao_periodo(parte[parte["ano"] >= 2009])

        if reda:
            dummy = _modelo_redacao_dummy(parte)
            pre = _regressao_periodo(parte[parte["ano"] <= 2008])
            if dummy is None:
                valores = [nome, "—", "—", "—", "—", "—", "—", "—"]
            else:
                modelo, _ = dummy
                valores = [
                    nome,
                    _fmt(pre[0].params.iloc[1]) if pre is not None else "—",
                    _fmt(pos[0].params.iloc[1]) if pos is not None else "—",
                    _fmt(modelo.params.get("ano", np.nan)),
                    _fmt_p(modelo.pvalues.get("ano", np.nan)),
                    _fmt(modelo.params.get("pos_2009", np.nan), 2),
                    _fmt_p(modelo.pvalues.get("pos_2009", np.nan)),
                    _fmt(modelo.rsquared),
                ]
        else:
            # CN, CH, LC e MT só têm série no período 2009–2025.
            if pos is None:
                valores = [nome, "—", "—", "—"]
            else:
                modelo_pos, _ = pos
                valores = [
                    nome,
                    _fmt(modelo_pos.params.iloc[1]),
                    _fmt_p(modelo_pos.pvalues.iloc[1]),
                    _fmt(modelo_pos.rsquared),
                ]

        linhas.append(html.Tr([
            html.Td(v, style={"padding": "6px 8px", "borderBottom": "1px solid #e2e8f0", "whiteSpace": "nowrap"})
            for v in valores
        ]))

    if reda:
        cabecalhos = [
            "Município", "Inclinação 1998–2008", "Inclinação 2009–2025",
            "Tendência comum OLS", "p-valor (ano)", "Degrau em 2009",
            "p-valor (degrau)", "R²",
        ]
        interpretacao = (
            "As inclinações mostram a variação anual estimada em cada período. "
            "O modelo OLS com dummy estima uma tendência anual comum e o deslocamento de nível associado a 2009. "
            "Os p-valores indicam a evidência estatística dos coeficientes; R² resume o ajuste do modelo."
        )
        limitacao = (
            "A normalização corrige a diferença de escala, mas não a mudança dos critérios de correção em 2009. "
            "Compare os períodos pré e pós-2009 com cautela."
        )
    else:
        cabecalhos = ["Município", "Inclinação 2009–2025 (pontos/ano)", "p-valor da tendência", "R²"]
        interpretacao = (
            "A inclinação representa a variação anual estimada por regressão linear no período disponível (2009–2025). "
            "O p-valor avalia a evidência estatística da tendência e R² resume o ajuste do modelo."
        )
        limitacao = (
            "As séries de Ciências da Natureza, Ciências Humanas, Linguagens e Matemática estão disponíveis a partir de 2009."
        )

    tabela = html.Div(
        html.Table([
            html.Thead(html.Tr([
                html.Th(t, style={"padding": "8px", "textAlign": "left", "background": "#f1f5f9", "borderBottom": "1px solid #cbd5e1"})
                for t in cabecalhos
            ])),
            html.Tbody(linhas),
        ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "12px"}),
        style={"overflowX": "auto", "width": "100%"},
    )
    return html.Div([
        html.Div(f"Tendências anuais — {disciplina}", style={"fontWeight": "700", "fontSize": "14px", "marginBottom": "8px"}),
        tabela,
        html.P(interpretacao, style={"margin": "10px 0 6px", "color": "#475569", "lineHeight": "1.45"}),
        html.P(limitacao, style={"marginBottom": "0", "fontWeight": "600", "color": "#92400e", "lineHeight": "1.45"}),
    ], style={"padding": "12px 14px", "background": "white", "border": "1px solid #e2e8f0", "borderRadius": "6px", "fontSize": "12px", "marginTop": "8px"})


def _mapa_cores_municipios(codigos):
    """Associa cor estável a cada município na ordem de seleção (ciclo de quatro)."""
    principais = CORES_MUNICIPIOS["principais"]
    variantes = CORES_MUNICIPIOS["variantes"]
    return {
        codigo: {"principal": principais[i % len(principais)],
                 "variante": variantes[i % len(variantes)]}
        for i, codigo in enumerate(codigos)
    }


def _clarear_cor(cor, proporcao=0.38):
    """Mistura uma cor Plotly com branco para gerar uma tonalidade mais clara."""
    cor = str(cor or "#636EFA").strip()
    if cor.startswith("#") and len(cor) == 7:
        rgb = tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))
    elif cor.startswith("rgb(") and cor.endswith(")"):
        rgb = tuple(int(float(v.strip())) for v in cor[4:-1].split(",")[:3])
    else:
        return cor
    claro = tuple(round(v + (255 - v) * proporcao) for v in rgb)
    return f"rgb({claro[0]}, {claro[1]}, {claro[2]})"

def _figura_vazia(mensagem):
    fig = go.Figure()
    fig.add_annotation(
        text=mensagem, x=0.5, y=0.5,
        xref="paper", yref="paper", showarrow=False,
    )
    fig.update_layout(template="plotly_white", height=380)
    return fig


def _figura_evolucao_participantes(painel, codigos, dependencia, nomes, serie=None):
    df = serie if serie is not None else _serie_participantes(painel, codigos, dependencia)
    if df.empty:
        return _figura_vazia("Não há dados de participação para a seleção.")

    fig = go.Figure()
    cores = _mapa_cores_municipios(codigos)
    for codigo, parte in df.groupby("codigo"):
        parte = parte.sort_values("ano")
        nome = nomes.get(codigo, codigo)
        cor = cores.get(codigo, {}).get("principal", CORES_MUNICIPIOS["principais"][0])
        fig.add_trace(go.Scatter(
            x=parte["ano"], y=parte["participantes"],
            mode="lines+markers", name=nome,
            line={"color": cor}, marker={"color": cor},
            hovertemplate="%{x}: %{y:,.0f}<extra>" + nome + "</extra>",
        ))
        reg = _regressao(parte["ano"], parte["participantes"])
        if reg is not None:
            ajustados, inclinacao, r2 = reg
            fig.add_trace(go.Scatter(
                x=parte["ano"], y=ajustados, mode="lines",
                line={"dash": "dash", "width": 1.8, "color": cor},
                name=f"Tendência — {nome}",
                hovertemplate="Tendência: %{y:,.0f}<extra>" + nome + "</extra>",
            ))

    fig.update_layout(
        template="plotly_white", height=390,
        title="Evolução do número de participantes",
        xaxis_title="Ano", yaxis_title="Participantes",
        legend={"title": "Município", "groupclick": "togglegroup"},
        margin=dict(l=45, r=20, t=55, b=45),
    )
    return fig


def _figura_evolucao_desempenho(grupo, codigos, dependencia, disciplina, nomes, serie=None):
    df = serie if serie is not None else _serie_desempenho(
        grupo, codigos, dependencia, DISCIPLINAS[disciplina]
    )
    if df.empty:
        return _figura_vazia("Não há dados de desempenho para essa avaliação."), html.Div()

    fig = go.Figure()
    cores = _mapa_cores_municipios(codigos)
    for codigo, parte in df.groupby("codigo"):
        parte = parte.sort_values("ano")
        nome = nomes.get(codigo, codigo)
        cor_base = cores.get(codigo, {}).get("principal", CORES_MUNICIPIOS["principais"][0])
        fig.add_trace(go.Scatter(
            x=parte["ano"], y=parte["media"],
            line={"color": cor_base}, marker={"color": cor_base},
            mode="lines+markers", name=nome,
            customdata=parte["n_validos"],
            hovertemplate=(
                "%{x}: %{y:.2f}<br>N válido: %{customdata:,.0f}"
                "<extra>" + nome + "</extra>"
            ),
        ))

        if disciplina == "Redação":
            # As duas variantes são configuráveis no dicionário CORES_MUNICIPIOS.
            cor_clara = cores.get(codigo, {}).get("variante", cor_base)
            periodos = [
                (parte[parte["ano"] <= 2008], "Tendência 1998–2008", cor_clara),
                (parte[parte["ano"] >= 2009], "Tendência 2009–2025", cor_base),
            ]


            # Uma entrada de legenda por município, compartilhada pelas duas regressões.
            legenda_tendencia_exibida = False
            grupo_tendencia = f"tendencias-{codigo}"

            for trecho, rotulo, cor in periodos:
                reg = _regressao_periodo(trecho)
                if reg is not None:
                    modelo_periodo, ajustados = reg
                    trecho_ordenado = trecho.sort_values("ano")
                    mostrar_legenda = not legenda_tendencia_exibida
                    fig.add_trace(go.Scatter(
                        x=trecho_ordenado["ano"], y=ajustados,
                        mode="lines",
                        line={"dash": "dash", "width": 2, "color": cor},
                        name=f"Tendências — {nome}",
                        legendgroup=grupo_tendencia,
                        showlegend=mostrar_legenda,
                        hovertemplate="Tendência: %{y:.2f}<extra>" + nome + "</extra>",
                    ))
                    if mostrar_legenda:
                        legenda_tendencia_exibida = True
        else:
            cor = cor_base
            reg = _regressao(parte["ano"], parte["media"])
            if reg is not None:
                ajustados, inclinacao, r2 = reg
                fig.add_trace(go.Scatter(
                    x=parte["ano"], y=ajustados, mode="lines",
                    line={"dash": "dash", "width": 1.8, "color": cor},
                    name=f"Tendência — {nome}",
                    hovertemplate="Tendência: %{y:.2f}<extra>" + nome + "</extra>",
                ))

    if disciplina == "Redação":
        fig.add_vline(
            x=2009, line_dash="dot", line_width=2, line_color="#64748b",
            annotation_text="Mudança de metodologia", annotation_position="top",
        )

    fig.update_layout(
        template="plotly_white", height=390,
        title=f"Evolução do desempenho — {disciplina}",
        xaxis_title="Ano", yaxis_title="Média",
        legend_title="Município",
        margin=dict(l=45, r=20, t=55, b=45),
    )
    resumo = _resumo_tendencias_disciplina(df, nomes, disciplina)
    return fig, resumo


def _figura_comparacao(painel, grupo, codigos, ano, dependencia, disciplina, nomes,
                       referencia=None, serie_participantes=None):
    """Compara participantes e distribuições por rede no ano selecionado."""
    from plotly.subplots import make_subplots

    participantes = (
        serie_participantes
        if serie_participantes is not None
        else _serie_participantes(painel, codigos, dependencia)
    )
    participantes = participantes[participantes["ano"] == int(ano)].copy()
    # A ordem do boxplot acompanha exatamente a ordem exibida nas barras.
    ordem_grafico = participantes["codigo"].drop_duplicates().tolist()
    ordem_grafico = [c for c in ordem_grafico if c in codigos]
    ordem_grafico += [c for c in codigos if c not in ordem_grafico]

    sufixo = DISCIPLINAS[disciplina]
    grupos_selecionados = DEPENDENCIAS.get(dependencia)
    if grupos_selecionados is None:
        grupos_selecionados = ["FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA"]
    grupos_selecionados = [g for g in grupos_selecionados if g in {
        "FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA"
    }]

    colunas = [
        "ano", "CO_MUNICIPIO_TERRITORIO", "tipo_grupo", "grupo",
        "disciplina", "media", "mediana", "q1", "q3", "std", "n_validos",
    ]
    stats = pd.DataFrame()
    if all(c in grupo.columns for c in colunas):
        stats = grupo.copy()
        stats["ano"] = pd.to_numeric(stats["ano"], errors="coerce")
        stats["codigo"] = _codigo(stats["CO_MUNICIPIO_TERRITORIO"])
        for coluna in ["tipo_grupo", "grupo", "disciplina"]:
            stats[coluna] = stats[coluna].astype(str).str.strip().str.upper()
        stats = stats[
            stats["tipo_grupo"].eq("ESCOLA")
            & stats["grupo"].isin(grupos_selecionados)
            & stats["disciplina"].eq(sufixo)
            & stats["codigo"].isin(codigos)
            & stats["ano"].eq(int(ano))
        ].copy()
        if referencia and "TIPO_REFERENCIA_TERRITORIAL" in stats.columns:
            stats = stats[
                stats["TIPO_REFERENCIA_TERRITORIAL"].astype(str).str.strip().str.upper()
                == str(referencia).strip().upper()
            ]
        for coluna in ["media", "mediana", "q1", "q3", "std", "n_validos"]:
            stats[coluna] = pd.to_numeric(stats[coluna], errors="coerce")
        stats = stats.dropna(subset=["media", "mediana", "q1", "q3"])
        stats = stats[
            stats["n_validos"].gt(0)
            & stats["q1"].le(stats["mediana"])
            & stats["mediana"].le(stats["q3"])
        ].copy()

        # Redação: escala 0–100 até 2008 e 0–1000 a partir de 2009.
        if sufixo == "REDACAO" and int(ano) <= 2008:
            for coluna in ["media", "mediana", "q1", "q3", "std"]:
                stats[coluna] *= 10

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Número de participantes", f"Distribuição das notas — {disciplina}"),
        horizontal_spacing=0.16,
    )
    cores = _mapa_cores_municipios(codigos)

    # Gráfico de participantes: uma barra por município, com a cor da série histórica.
    if not participantes.empty:
        parte = participantes.copy()
        parte["municipio"] = parte["codigo"].map(nomes)
        parte["cor"] = parte["codigo"].map({c: cores[c]["principal"] for c in cores})
        fig.add_trace(go.Bar(
            x=parte["municipio"], y=parte["participantes"],
            name="Participantes", marker={"color": parte["cor"].tolist()},
            showlegend=False,
            hovertemplate="%{x}<br>Participantes: %{y:,.0f}<extra></extra>",
        ), row=1, col=1)

    # Boxplots lado a lado: cada rede ocupa uma posição dentro do município.
    # A posição numérica evita sobreposição de traces de estatísticas resumidas.
    if not stats.empty and grupos_selecionados:
        stats["municipio"] = stats["codigo"].map(nomes)
        n_grupos = len(grupos_selecionados)
        largura_slot = 0.22
        simbolos_grupos = {
            "FEDERAL": "circle",
            "ESTADUAL": "diamond",
            "MUNICIPAL": "triangle-up",
            "PRIVADA": "square",
        }
        # Legenda independente: o símbolo identifica a rede; a cor identifica o município.
        for grupo_nome in grupos_selecionados:
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers",
                marker={"symbol": simbolos_grupos.get(grupo_nome, "circle"),
                        "size": 10, "color": "#475569",
                        "line": {"color": "#334155", "width": 1}},
                name=grupo_nome.capitalize(), showlegend=True,
                legendgroup=f"rede-{grupo_nome}",
                hoverinfo="skip",
            ), row=1, col=2)

        for indice_municipio, codigo in enumerate(ordem_grafico):
            parte_municipio = stats[stats["codigo"] == codigo]
            if parte_municipio.empty:
                continue
            nome = nomes.get(codigo, codigo)
            cor = cores.get(codigo, {}).get("principal", CORES_MUNICIPIOS["principais"][0])
            for indice_grupo, grupo_nome in enumerate(grupos_selecionados):
                registros = parte_municipio[parte_municipio["grupo"] == grupo_nome]
                if registros.empty:
                    continue
                registro = registros.iloc[0]
                iqr = float(registro["q3"] - registro["q1"])
                limite_inferior = float(registro["q1"] - 1.5 * iqr)
                limite_superior = float(registro["q3"] + 1.5 * iqr)
                posicao = indice_municipio + (indice_grupo - (n_grupos - 1) / 2) * largura_slot
                fig.add_trace(go.Box(
                    x=[posicao],
                    q1=[registro["q1"]], median=[registro["mediana"]], q3=[registro["q3"]],
                    lowerfence=[limite_inferior], upperfence=[limite_superior],
                    name=f"{nome} — {grupo_nome}", width=largura_slot * 0.88,
                    line={"color": cor, "width": 2}, fillcolor=cor, opacity=0.58,
                    whiskerwidth=0.65, boxpoints=False, showlegend=False,
                    customdata=[[registro["media"], registro["std"], registro["n_validos"], grupo_nome]],
                    hovertemplate=(
                        f"{nome}<br>Dependência: %{{customdata[3]}}"
                        "<br>Limite inferior teórico: %{lowerfence:.2f}"
                        "<br>Q1: %{q1:.2f}<br>Mediana: %{median:.2f}"
                        "<br>Média: %{customdata[0]:.2f}<br>Q3: %{q3:.2f}"
                        "<br>Limite superior teórico: %{upperfence:.2f}"
                        "<br>Desvio padrão: %{customdata[1]:.2f}"
                        "<br>N válido: %{customdata[2]:,.0f}<extra></extra>"
                    ),
                ), row=1, col=2)
                fig.add_trace(go.Scatter(
                    x=[posicao], y=[registro["media"]], mode="markers",
                    marker={"symbol": simbolos_grupos.get(grupo_nome, "circle"),
                            "size": 10, "color": cor,
                            "line": {"color": "#1f2937", "width": 1}},
                    showlegend=False,
                    customdata=[[grupo_nome, nome]],
                    hovertemplate="%{customdata[1]}<br>Dependência: %{customdata[0]}<br>Média: %{y:.2f}<extra></extra>",
                ), row=1, col=2)
    else:
        fig.add_annotation(
            text="Não há estatísticas disponíveis para os municípios e filtros selecionados.",
            x=0.75, y=0.5, xref="paper", yref="paper", showarrow=False,
            font={"color": "#64748b", "size": 12},
        )

    fig.update_layout(
        template="plotly_white", height=430,
        title=f"Comparação municipal — {ano}", showlegend=True,
        legend={"title": {"text": "Dependência administrativa"},
                "orientation": "v", "x": 1.01, "y": 1},
        boxmode="overlay", margin=dict(l=45, r=155, t=70, b=100),
    )
    fig.update_xaxes(tickangle=-35, row=1, col=1)
    fig.update_xaxes(
        tickmode="array", tickvals=list(range(len(ordem_grafico))),
        ticktext=[nomes.get(c, c) for c in ordem_grafico],
        categoryorder="array", categoryarray=[nomes.get(c, c) for c in ordem_grafico],
        range=[-0.6, max(len(ordem_grafico) - 0.4, 0.6)],
        tickangle=-35, title_text="Município", row=1, col=2,
    )
    fig.update_yaxes(title_text="Participantes", row=1, col=1)
    fig.update_yaxes(title_text="Nota", row=1, col=2, rangemode="tozero")
    return fig


def _figura_dispersao(painel, grupo, ano, dependencia, disciplina, nomes,
                       codigos_destaque=None):
    """Dispersão por dependência: círculo=pública; quadrado=privada."""
    codigos = list(nomes.keys())
    codigos_destaque = list(codigos_destaque or [])

    # A dispersão sempre separa as redes pública e privada, independentemente
    # do filtro de dependência usado nas demais visualizações.
    df_grupo = grupo.copy()
    for col in ["tipo_grupo", "grupo", "disciplina"]:
        df_grupo[col] = df_grupo[col].astype(str).str.strip().str.upper()

    df_grupo["ano"] = pd.to_numeric(df_grupo["ano"], errors="coerce")
    df_grupo["media"] = pd.to_numeric(df_grupo["media"], errors="coerce")
    df_grupo["n_validos"] = pd.to_numeric(df_grupo["n_validos"], errors="coerce")
    df_grupo["codigo"] = _codigo(df_grupo["CO_MUNICIPIO_TERRITORIO"])

    df_grupo = df_grupo[
        (df_grupo["tipo_grupo"] == "ESCOLA")
        & (df_grupo["ano"] == int(ano))
        & (df_grupo["disciplina"] == DISCIPLINAS[disciplina])
        & (df_grupo["codigo"].isin(codigos))
        & (df_grupo["grupo"].isin(["FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA"]))
        & df_grupo["media"].notna()
        & df_grupo["n_validos"].gt(0)
    ].copy()

    if df_grupo.empty:
        return _figura_vazia(
            "Não há dados por dependência administrativa para este ano e disciplina."
        )

    df_grupo["soma_ponderada"] = df_grupo["media"] * df_grupo["n_validos"]

    # Rede pública: média ponderada de Federal, Estadual e Municipal.
    publica = (
        df_grupo[df_grupo["grupo"].isin(["FEDERAL", "ESTADUAL", "MUNICIPAL"])]
        .groupby("codigo", as_index=False)
        .agg(
            soma_ponderada=("soma_ponderada", "sum"),
            n_validos=("n_validos", "sum"),
        )
    )
    publica["media"] = publica["soma_ponderada"] / publica["n_validos"]
    publica["dependencia_plot"] = "Pública"
    publica["simbolo"] = "circle"

    # Rede privada: já corresponde a uma única categoria agregada.
    privada = (
        df_grupo[df_grupo["grupo"] == "PRIVADA"]
        .groupby("codigo", as_index=False)
        .agg(
            soma_ponderada=("soma_ponderada", "sum"),
            n_validos=("n_validos", "sum"),
        )
    )
    privada["media"] = privada["soma_ponderada"] / privada["n_validos"]
    privada["dependencia_plot"] = "Privada"
    privada["simbolo"] = "square"

    df = pd.concat([publica, privada], ignore_index=True)
    df = df[
        df["n_validos"].gt(0)
        & df["media"].notna()
        & np.isfinite(df["media"])
    ].copy()

    if df.empty:
        return _figura_vazia(
            "Não há observações válidas para as redes pública e privada."
        )

    df["municipio"] = df["codigo"].map(nomes)
    df["cor"] = "#B8C0CC"
    df["selecionado"] = df["codigo"].isin(codigos_destaque)

    # A referência dos quadrantes agora é formada por pontos de dependência
    # com mais de LIMITE_N_QUADRANTES notas válidas.
    df_referencia = df[df["n_validos"] > LIMITE_N_QUADRANTES].copy()
    if df_referencia.empty:
        return _figura_vazia(
            "Não há pontos de dependência com mais de "
            f"{LIMITE_N_QUADRANTES} notas válidas para calcular os quadrantes."
        )

    mediana_n = float(df_referencia["n_validos"].median())
    mediana_media = float(df_referencia["media"].median())
    cores_destaque = _mapa_cores_municipios(codigos_destaque)

    for codigo in codigos_destaque:
        cor = cores_destaque.get(codigo, {}).get(
            "principal", CORES_MUNICIPIOS["principais"][0]
        )
        df.loc[df["codigo"] == codigo, "cor"] = cor

    fig = go.Figure()
    df_contexto = df[~df["selecionado"]]
    if not df_contexto.empty:
        for dependencia_plot, simbolo in [("Pública", "circle"), ("Privada", "square")]:
            parte = df_contexto[df_contexto["dependencia_plot"] == dependencia_plot]
            if parte.empty:
                continue
            fig.add_trace(go.Scatter(
                x=parte["n_validos"],
                y=parte["media"],
                mode="markers",
                name=f"Demais municípios — {dependencia_plot.lower()}",
                marker={
                    "size": 7, "color": "#B8C0CC", "opacity": 0.55,
                    "symbol": simbolo,
                    "line": {"width": 0.4, "color": "white"},
                },
                customdata=np.column_stack([
                    parte["municipio"], parte["dependencia_plot"],
                ]),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Dependência: %{customdata[1]}<br>"
                    "Notas válidas: %{x:,.0f}<br>"
                    f"Média de {disciplina}: " + "%{y:.2f}<extra></extra>"
                ),
            ))

    # Municípios selecionados: cor identifica município; símbolo identifica rede.
    for codigo in codigos_destaque:
        parte_municipio = df[df["codigo"] == codigo]
        if parte_municipio.empty:
            continue
        nome = nomes.get(codigo, codigo)
        cor = cores_destaque.get(codigo, {}).get(
            "principal", CORES_MUNICIPIOS["principais"][0]
        )
        for dependencia_plot, simbolo in [("Pública", "circle"), ("Privada", "square")]:
            parte = parte_municipio[
                parte_municipio["dependencia_plot"] == dependencia_plot
            ]
            if parte.empty:
                continue
            fig.add_trace(go.Scatter(
                x=parte["n_validos"],
                y=parte["media"],
                mode="markers",
                name=f"{nome} — {dependencia_plot.lower()}",
                marker={
                    "size": 13, "color": cor, "opacity": 1,
                    "line": {"width": 1.8, "color": "#172033"},
                    "symbol": simbolo,
                },
                customdata=np.column_stack([
                    parte["municipio"], parte["dependencia_plot"],
                ]),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Dependência: %{customdata[1]}<br>"
                    "Notas válidas: %{x:,.0f}<br>"
                    f"Média de {disciplina}: " + "%{y:.2f}<extra></extra>"
                ),
            ))

    fig.add_vline(
        x=mediana_n, line_dash="dash", line_color="#64748b", line_width=1.5
    )
    fig.add_hline(
        y=mediana_media, line_dash="dash", line_color="#64748b", line_width=1.5
    )

    anotacoes = [
        (0.02, 0.98, "Menor N válido<br>Maior desempenho", "left", "top"),
        (0.98, 0.98, "Maior N válido<br>Maior desempenho", "right", "top"),
        (0.02, 0.02, "Menor N válido<br>Menor desempenho", "left", "bottom"),
        (0.98, 0.02, "Maior N válido<br>Menor desempenho", "right", "bottom"),
    ]
    for x, y, texto, xanchor, yanchor in anotacoes:
        fig.add_annotation(
            x=x, y=y, xref="paper", yref="paper", showarrow=False,
            text=texto, xanchor=xanchor, yanchor=yanchor,
            font={"size": 10, "color": "#64748b"},
            bgcolor="rgba(255,255,255,0.75)",
        )

    fig.update_xaxes(type="log", title_text="Notas válidas por dependência (escala logarítmica)")
    fig.update_yaxes(title_text=f"Média de {disciplina}")
    fig.update_layout(
        template="plotly_white", height=500,
        margin=dict(t=65, b=55, l=65, r=35),
        showlegend=True,
        legend={"title": "Município e dependência"},
    )

    if (
        len(df_referencia) >= 2
        and df_referencia["n_validos"].nunique() > 1
        and df_referencia["media"].nunique() > 1
    ):
        correlacao = df_referencia[
            ["n_validos", "media"]
        ].corr(method="pearson").iloc[0, 1]
        resumo = (
            f"Mediana de notas válidas (N > {LIMITE_N_QUADRANTES}): "
            f"{mediana_n:,.0f} | "
            f"Mediana de desempenho: {mediana_media:.2f} | "
            f"Pearson no mesmo conjunto: {correlacao:.3f} | "
            f"Pontos na referência: {len(df_referencia)}."
        ).replace(",", ".")
    else:
        resumo = (
            f"Mediana de notas válidas (N > {LIMITE_N_QUADRANTES}): "
            f"{mediana_n:,.0f} | "
            f"Mediana de desempenho: {mediana_media:.2f} | "
            f"Pontos na referência: {len(df_referencia)}."
        ).replace(",", ".")

    n_excluidos = int((df["n_validos"] <= LIMITE_N_QUADRANTES).sum())
    resumo += (
        f" Quadrantes calculados com pontos de dependência com N válido > "
        f"{LIMITE_N_QUADRANTES}; pontos abaixo desse limite continuam visíveis. "
        "Círculos representam a rede pública e quadrados a privada. "
        "A associação não indica causalidade."
    )
    if n_excluidos:
        resumo += f" Pontos abaixo do limite: {n_excluidos}."
    return fig, resumo


def registrar_callbacks_analise(app, carregar_dados):
    @app.callback(
        Output("analise-municipio-principal", "options"),
        Output("analise-municipios-comparacao", "options"),
        Output("analise-municipio-principal", "value"),
        Input("seletor-referencia-territorial", "value"),
        Input("seletor-uf", "value"),
        State("analise-municipio-principal", "value"),
    )
    @medir_callback("análise · atualizar_municipios (lista de municípios)")
    def atualizar_municipios(referencia, uf, atual):
        dados = carregar_dados(uf, referencia=referencia)
        opcoes_df = _painel_municipios(dados["painel"])
        opcoes = [
            {"label": nome, "value": codigo}
            for codigo, nome in zip(
                opcoes_df["codigo"], opcoes_df["NO_MUNICIPIO_TERRITORIO"]
            )
        ]
        codigos = {x["value"] for x in opcoes}
        principal = atual if atual in codigos else (opcoes[0]["value"] if opcoes else None)
        return opcoes, opcoes, principal

    @app.callback(
        Output("analise-kpis", "children"),
        Output("analise-evolucao-participantes", "figure"),
        Output("analise-evolucao-desempenho", "figure"),
        Output("analise-tendencia-redacao", "children"),
        Output("analise-comparacao", "figure"),
        Output("analise-dispersao", "figure"),
        Output("analise-correlacao", "children"),
        State("seletor-referencia-territorial", "value"),
        Input("analise-municipio-principal", "value"),
        Input("analise-municipios-comparacao", "value"),
        Input("analise-dependencia", "value"),
        Input("analise-disciplina", "value"),
        Input("analise-ano", "value"),
        State("seletor-uf", "value"),
        State("url", "pathname"),
    )
    @medir_callback("análise · atualizar_analise (7 saídas)")
    def atualizar_analise(
        referencia, principal, comparacao, dependencia,
        disciplina, ano, uf, pathname
    ):
        if pathname not in ("/analise-municipal", "/analise") or not principal:
            return (no_update,) * 7

        dados = carregar_dados(uf, referencia=referencia)
        painel = dados["painel"].copy()
        grupo = dados["grupo"].copy()

        nomes = _nomes_municipios(painel)
        codigos = [principal] + [
            c for c in (comparacao or [])
            if c != principal
        ][:4]
        nomes_selecionados = {c: nomes.get(c, c) for c in codigos}

        painel["codigo"] = _codigo(painel["CO_MUNICIPIO_TERRITORIO"])
        painel["ano"] = pd.to_numeric(painel["ano"], errors="coerce")
        atual = painel[
            (painel["codigo"] == principal)
            & (painel["ano"] == int(ano))
        ]

        # Calcula as séries uma única vez e reutiliza nas figuras e nos KPIs.
        with etapa("análise: séries (participantes + desempenho)"):
            serie_part = _serie_participantes(painel, codigos, dependencia)
            serie_disc = _serie_desempenho(
                grupo, codigos, dependencia, DISCIPLINAS[disciplina]
            )
        serie_disc_principal = serie_disc[serie_disc["codigo"] == principal]
        serie_disc_ano = serie_disc_principal[serie_disc_principal["ano"] == int(ano)]
        media = (
            np.average(serie_disc_ano["media"], weights=serie_disc_ano["n_validos"])
            if not serie_disc_ano.empty else np.nan
        )
        n_validos = (
            int(serie_disc_ano["n_validos"].sum())
            if not serie_disc_ano.empty else 0
        )

        serie_part_principal = serie_part[serie_part["codigo"] == principal]
        total_ano = serie_part_principal[serie_part_principal["ano"] == int(ano)]

        total = (total_ano["participantes"].sum() if not total_ano.empty else np.nan)

        ano_atual = int(ano)
        ano_anterior = ano_atual - 1

        participantes_atual = serie_part_principal.loc[
            serie_part_principal["ano"] == ano_atual, "participantes"
        ].sum()

        dados_anterior = serie_part_principal.loc[
            serie_part_principal["ano"] == ano_anterior, "participantes"
        ]

        participantes_anterior = (dados_anterior.sum() if not dados_anterior.empty else np.nan)

        variacao = (
            (participantes_atual / participantes_anterior - 1) * 100
            if pd.notna(participantes_anterior)
               and participantes_anterior > 0
            else np.nan)

        #valores = serie_part["participantes"].dropna()

        #primeiro = valores.iloc[0] if not valores.empty else np.nan
        #ultimo = valores.iloc[-1] if not valores.empty else np.nan
        #variacao = (
         #   (ultimo / primeiro - 1) * 100
         #   if pd.notna(primeiro) and primeiro != 0 and pd.notna(ultimo)
         #   else np.nan
       # )

        kpis = [
            _card("Participantes no ano", total, f"Ano {ano}"),
            _card("Variação anual de participantes",variacao,"Em relação ao ano anterior (%)"),
            _card("Anos com dados", int(serie_part_principal["ano"].nunique()), "Série de participação"),
            _card(f"Média — {disciplina}", media, f"N válido: {n_validos:,}".replace(",", ".")),

        ]

        fig_part = _figura_evolucao_participantes(
            painel, codigos, dependencia, nomes_selecionados, serie=serie_part
        )
        fig_desempenho, resumo_tendencia_redacao = _figura_evolucao_desempenho(
            grupo, codigos, dependencia, disciplina, nomes_selecionados,
            serie=serie_disc,
        )
        with etapa("análise: figura de comparação"):
            fig_comparacao = _figura_comparacao(
                painel, grupo, codigos, ano, dependencia, disciplina,
                nomes_selecionados, referencia, serie_participantes=serie_part,
            )
        with etapa("análise: dispersão + regressão"):
            dispersao_resultado = _figura_dispersao(
                painel, grupo, ano, dependencia, disciplina, nomes,
                codigos_destaque=codigos,
            )
        if isinstance(dispersao_resultado, tuple):
            fig_dispersao, resumo_corr = dispersao_resultado
        else:
            fig_dispersao, resumo_corr = dispersao_resultado, ""

        resumo = html.Div(
            resumo_corr,
            style={
                "padding": "10px 12px",
                "background": "white",
                "border": "1px solid #e2e8f0",
                "borderRadius": "6px",
                "fontSize": "13px",
            },
        )

        return (
            kpis, fig_part, fig_desempenho, resumo_tendencia_redacao,
            fig_comparacao, fig_dispersao, resumo
        )
