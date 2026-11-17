#visão_geral_layout.py
from dash import html, dcc
from dash_utils.ufs import nome_uf
import pandas as pd


def _cartao_indicador(titulo, valor, descricao):
    return html.Div(
        [
            html.P(
                titulo,
                style={"fontSize": "13px", "color": "#64748b", "marginBottom": "8px"}
            ),
            html.H2(
                valor,
                style={"fontSize": "28px", "color": "#1e293b", "margin": "0"}
            ),
            html.P(
                descricao,
                style={"fontSize": "12px", "color": "#94a3b8", "marginTop": "8px"}
            )
        ],
        style={
            "backgroundColor": "#ffffff",
            "border": "1px solid #e2e8f0",
            "borderRadius": "10px",
            "padding": "20px",
            "flex": "1",
            "minWidth": "180px"
        }
    )


def _nome_uf_dados(dados):
    return nome_uf(dados["uf"])

def criar_layout(dados, graficos):
    uf_nome = _nome_uf_dados(dados)
    painel = dados["painel"].copy()
    painel["ano"] = painel["ano"].astype("Int64")

    anos = sorted(painel["ano"].dropna().unique())
    ano_inicial = int(min(anos))
    ano_final = int(max(anos))

    colunas_dependencia = [
        "n_escola_federal",
        "n_escola_estadual",
        "n_escola_municipal",
        "n_escola_privada",
        "n_escola_nao_informada",
    ]
    for coluna in ["n_participantes", *colunas_dependencia]:
        painel[coluna] = pd.to_numeric(painel[coluna], errors="coerce").fillna(0)

    total_participantes = int(painel["n_participantes"].sum())
    total_publicas = int(
        painel[["n_escola_federal", "n_escola_estadual", "n_escola_municipal"]].sum().sum()
    )
    total_privadas = int(painel["n_escola_privada"].sum())
   # total_nao_informadas = int(painel["n_escola_nao_informada"].sum())

    total_nao_informadas = (
            total_participantes
            - total_publicas
            - total_privadas
    )

    pct_publicas = (100 * total_publicas / total_participantes) if total_participantes else 0
    pct_privadas = (100 * total_privadas / total_participantes) if total_participantes else 0
    pct_nao_informadas = (100 * total_nao_informadas / total_participantes) if total_participantes else 0

    return html.Div(
        [
            html.Div(
                [
                    html.H1(f"ENEM em {uf_nome}", style={"color": "#0f172a"}),
                    html.P(
                        "Panorama histórico da participação e do desempenho dos participantes.",
                        style={"color": "#64748b"}
                    )
                ],
                style={"marginBottom": "30px"}
            ),
            html.Div(
                [
                    html.H3("Visão geral"),
                    html.P(
                        f"Esta análise contempla os resultados do ENEM entre {ano_inicial} e {ano_final}, "
                        f"considerando os municípios do estado de {uf_nome}."
                    ),
                    html.P(
                        "O painel apresenta indicadores de participação, perfil dos participantes "
                        "e desempenho nas avaliações."
                    )
                ],
                style={
                    "backgroundColor": "#f1f5f9",
                    "padding": "20px",
                    "borderRadius": "10px",
                    "marginBottom": "25px"
                }
            ),
            html.H3("Panorama histórico"),
            html.Div(
                [
                    _cartao_indicador(
                        "Total de participantes",
                        f"{total_participantes:,}".replace(",", "."),
                        f"Total registrado entre {ano_inicial} e {ano_final}"
                    ),
                    _cartao_indicador(
                        "Participantes da rede pública",
                        f"{total_publicas:,}".replace(",", "."),
                        f"{pct_publicas:.1f}% do total de participantes"
                    ),
                    _cartao_indicador(
                        "Participantes da rede privada",
                        f"{total_privadas:,}".replace(",", "."),
                        f"{pct_privadas:.1f}% do total de participantes"
                    ),
                    _cartao_indicador(
                        "Dependência não informada",
                        f"{total_nao_informadas:,}".replace(",", "."),
                        f"{pct_nao_informadas:.1f}% do total de participantes"
                    )
                ],
                style={
                    "display": "flex", "flexWrap": "wrap", "gap": "15px",
                    "marginBottom": "12px"
                }
            ),
            html.P(
                "Os participantes com dependência administrativa não informada são apresentados "
                "em indicador próprio e não são atribuídos às redes pública ou privada.",
                style={
                    "fontSize": "12px", "color": "#64748b",
                    "marginTop": "0", "marginBottom": "35px"
                }
            ),
            # PARTICIPAÇÃO
            html.Div(
                [
                    html.H3("Participação no ENEM"),
                    html.P(f"Evolução histórica do número de participantes registrados em {uf_nome}."),
                    dcc.Graph(
                        figure=graficos["participacao"],
                        config={"displayModeBar": True}
                    )
                ],
                style={"marginBottom": "35px"}
            ),
            # DESEMPENHO
            html.Div(
                [
                    html.H3("Desempenho dos participantes"),
                    html.P("Evolução histórica das notas médias estaduais de Redação."),
                    # REDAÇÃO: MODELO ANTIGO E NOVO
                    html.Div(
                        [
                            dcc.Graph(
                                figure=graficos["redacao_antiga"],
                                config={"displayModeBar": True},
                                style={"width": "100%"}
                            ),
                            dcc.Graph(
                                figure=graficos["redacao_nova"],
                                config={"displayModeBar": True},
                                style={"width": "100%"}
                            )
                        ],
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "11fr 17fr",
                            "gap": "15px",
                            "alignItems": "start",
                            "width": "100%"
                        }
                    ),
                    html.P(
                        "As médias estaduais são ponderadas pelo número de notas válidas em cada município. "
                        "Os gráficos utilizam escalas independentes: 0–100 no modelo antigo e 0–1000 no novo modelo.",
                        style={
                            "fontSize": "13px", "color": "#64748b", "marginTop": "10px"
                        }
                    ),
                    # PROVA OBJETIVA E QUATRO ÁREAS
                    html.H4(
                        "Prova objetiva e áreas de conhecimento",
                        style={"marginTop": "35px"}
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                figure=graficos["objetiva"],
                                config={"displayModeBar": True},
                                style={"width": "100%"}
                            ),
                            dcc.Graph(
                                figure=graficos["areas"],
                                config={"displayModeBar": True},
                                style={"width": "100%"}
                            )
                        ],
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "11fr 17fr",
                            "gap": "15px",
                            "alignItems": "start",
                            "width": "100%"
                        }
                    )

                    ,
                    # COMPARAÇÃO: PÚBLICO X PRIVADO
                    html.H3(
                        "Desempenho por dependência administrativa",
                        style={"marginTop": "45px"}
                    ),
                    html.H4("Escolas públicas x escolas privadas"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H5("1998–2008"),
                                    dcc.Graph(figure=graficos["pp_redacao_antigo"], config={"displayModeBar": True}),
                                    dcc.Graph(
                                        figure=graficos["pp_provas_antigo"],
                                        config={"displayModeBar": True},
                                        style={"width": "100%", "marginTop": "60px"}
                                    )
                                ]
                            ),
                            html.Div(
                                [
                                    html.H5("2009–2025"),
                                    dcc.Graph(figure=graficos["pp_redacao_novo"], config={"displayModeBar": True}),
                                    html.Label("Área de conhecimento"),
                                    dcc.Dropdown(
                                        id="seletor-pp-area",
                                        options=[
                                            {"label": "Ciências da Natureza (CN)", "value": "CN"},
                                            {"label": "Ciências Humanas (CH)", "value": "CH"},
                                            {"label": "Linguagens (LC)", "value": "LC"},
                                            {"label": "Matemática (MT)", "value": "MT"}
                                        ],
                                        value="CN",
                                        clearable=False,
                                        searchable=False,
                                        style={"maxWidth": "320px", "marginBottom": "8px"}
                                    ),
                                    dcc.Store(
                                        id="dados-pp-areas",
                                        data=graficos["pp_areas_dados"]
                                    ),
                                    dcc.Graph(
                                        id="grafico-pp-area",
                                        figure=graficos["pp_areas"],
                                        config={"displayModeBar": True}
                                    )
                                ]
                            )
                        ],
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "11fr 17fr",
                            "gap": "15px",
                            "alignItems": "start",
                            "width": "100%"
                        }
                    ),
                    html.P(
                        "O grupo público reúne as dependências municipal, estadual e federal. "
                        "A categoria não informada não foi incorporada às comparações.",
                        style={"fontSize": "13px", "color": "#64748b", "marginTop": "8px"}
                    ),
                    # COMPARAÇÃO ENTRE REDES PÚBLICAS
                    html.H4(
                        "Comparação entre as redes públicas",
                        style={"marginTop": "35px"}
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H5("1998–2008"),
                                    dcc.Graph(figure=graficos["redes_redacao_antigo"], config={"displayModeBar": True}),
                                    dcc.Graph(
                                        figure=graficos["redes_provas_antigo"],
                                        config={"displayModeBar": True},
                                        style={"width": "100%", "marginTop": "60px"}
                                    )
                                ]
                            ),
                            html.Div(
                                [
                                    html.H5("2009–2025"),
                                    dcc.Graph(figure=graficos["redes_redacao_novo"], config={"displayModeBar": True}),
                                    html.Label("Área de conhecimento"),
                                    dcc.Dropdown(
                                        id="seletor-redes-publicas-area",
                                        options=[
                                            {"label": "Ciências da Natureza (CN)", "value": "CN"},
                                            {"label": "Ciências Humanas (CH)", "value": "CH"},
                                            {"label": "Linguagens (LC)", "value": "LC"},
                                            {"label": "Matemática (MT)", "value": "MT"}
                                        ],
                                        value="CN",
                                        clearable=False,
                                        searchable=False,
                                        style={"maxWidth": "320px", "marginBottom": "8px"}
                                    ),
                                    dcc.Store(
                                        id="dados-redes-publicas-areas",
                                        data=graficos["redes_areas_dados"]
                                    ),
                                    dcc.Graph(
                                        id="grafico-redes-publicas-area",
                                        figure=graficos["redes_areas"],
                                        config={"displayModeBar": True}
                                    )
                                ]
                            )
                        ],
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "11fr 17fr",
                            "gap": "15px",
                            "alignItems": "start",
                            "width": "100%"
                        }
                    )
                ],
                style={"marginBottom": "35px"}
            ),
            # NOTA METODOLÓGICA
            html.Div(
                [
                    html.H4("Nota metodológica"),
                    html.P(
                        "A estrutura das avaliações do ENEM mudou ao longo do período analisado. "
                        "Entre 1998 e 2008, os dados contemplam prova objetiva e redação. A partir de 2009, "
                        "contemplam Ciências da Natureza, Ciências Humanas, Linguagens, Matemática e redação."
                    ),
                    html.P(
                        "Também ocorreram mudanças nas referências territoriais e na estrutura das bases de dados. "
                        "Essas diferenças serão consideradas nas comparações históricas."
                    )
                ],
                style={
                    "backgroundColor": "#fff7ed",
                    "border": "1px solid #fed7aa",
                    "padding": "20px",
                    "borderRadius": "10px",
                    "marginTop": "20px"
                }
            )
        ],
        style={
            "maxWidth": "1400px",
            "margin": "0 auto",
            "padding": "30px",
            "fontFamily": "Arial, sans-serif",
            "backgroundColor": "#f8fafc",
            "minHeight": "100vh"
        }
    )
