#visao_geral_graficos.py
import os
import psutil

import pandas as pd
import plotly.express as px
'''
add bloco de analise de memoria ram
'''

_PROCESSO = psutil.Process(os.getpid())
_RAM_LOG_ATIVO = os.environ.get("ENEM_RAM_LOG", "0") == "1"


def _registrar_memoria(etapa):
    """Registra RSS/USS somente quando ENEM_RAM_LOG=1."""
    if not _RAM_LOG_ATIVO:
        return
    memoria = _PROCESSO.memory_full_info()
    rss = memoria.rss / (1024 ** 2)
    uss = memoria.uss / (1024 ** 2)
    print(f"[MEMORIA] {etapa} | RSS={rss:.1f} MB | USS={uss:.1f} MB", flush=True)


def _media_estadual_ponderada(df, coluna_media, coluna_validos, anos=None):
    """Calcula a média estadual ponderada pelo número de notas válidas."""
    temp = df[["ano", coluna_media, coluna_validos]].copy()

    temp[coluna_media] = pd.to_numeric(temp[coluna_media], errors="coerce")
    temp[coluna_validos] = pd.to_numeric(temp[coluna_validos], errors="coerce")

    mascara = (
        temp[coluna_media].notna()
        & temp[coluna_validos].notna()
        & (temp[coluna_validos] > 0)
    )

    if anos is not None:
        mascara &= temp["ano"].between(*anos)

    temp = temp.loc[mascara].copy()
    temp["soma_ponderada"] = temp[coluna_media] * temp[coluna_validos]

    anual = (
        temp.groupby("ano", as_index=False)
        .agg(
            soma_ponderada=("soma_ponderada", "sum"),
            notas_validas=(coluna_validos, "sum")
        )
    )

    anual["media_estadual"] = anual["soma_ponderada"] / anual["notas_validas"]
    return anual.sort_values("ano")



def criar_grafico_area_selecionada(registros, disciplina, comparacao):
    """Cria gráfico de uma única área para a comparação selecionada."""
    df = pd.DataFrame(registros or [])
    df = df[df["disciplina"] == disciplina].copy() if not df.empty else df

    titulos = {"CN": "Ciências da Natureza", "CH": "Ciências Humanas", "LC": "Linguagens", "MT": "Matemática"}
    titulo_area = titulos.get(disciplina, disciplina)

    if comparacao == "publico_privado":
        cores = {"Público": "#2474a6", "Privado": "#e39b38"}
        titulo = f"{titulo_area} — Público x Privado (2009–2025)"
        line_dash = "categoria"
        line_dash_map = {"Público": "solid", "Privado": "dash"}
    else:
        cores = {"Municipal": "#269b78", "Estadual": "#2474a6", "Federal": "#9a75c9"}
        titulo = f"{titulo_area} — Redes públicas (2009–2025)"
        line_dash = None
        line_dash_map = None

    if df.empty:
        fig = px.line(title=f"{titulo} — sem dados disponíveis")
        fig.update_layout(template="plotly_white", height=420)
        return fig

    fig = px.line(
        df,
        x="ano",
        y="media_estadual",
        color="categoria",
        line_dash=line_dash,
        line_dash_map=line_dash_map,
        markers=True,
        color_discrete_map=cores,
        labels={"ano": "Ano", "media_estadual": "Nota média", "categoria": "Dependência administrativa"},
        title=titulo
    )
    fig.update_traces(
        line={"width": 2.8},
        marker={"size": 6},
        hovertemplate="Ano: %{x}<br>Média ponderada: %{y:.2f}<extra></extra>"
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=45, r=20, t=65, b=65),
        hovermode="x unified",
        xaxis=dict(title="Ano", dtick=1, showgrid=False),
        yaxis=dict(title="Nota média", range=[0, 1000]),
        legend=dict(title="", orientation="h", y=-0.25)
    )
    return fig


def criar_graficos(dados):
    _registrar_memoria("Visão Geral | entrada criar_graficos")

    painel = dados["painel"].copy()
    _registrar_memoria("Visão Geral | após cópia do painel")

    painel["ano"] = pd.to_numeric(painel["ano"], errors="coerce")
    graficos = {}

    # Participação anual por dependência administrativa e abrangência municipal
    colunas_participacao = [
        "n_participantes",
        "n_escola_federal",
        "n_escola_estadual",
        "n_escola_municipal",
        "n_escola_privada",
    ]
    for coluna in colunas_participacao:
        painel[coluna] = pd.to_numeric(painel[coluna], errors="coerce").fillna(0)

    participacao_anual = (
        painel.groupby("ano", as_index=False)
        .agg(
            total=("n_participantes", "sum"),
            federal=("n_escola_federal", "sum"),
            estadual=("n_escola_estadual", "sum"),
            municipal=("n_escola_municipal", "sum"),
            privada=("n_escola_privada", "sum"),
            municipios=("CO_MUNICIPIO_TERRITORIO", "nunique"),
        )
        .sort_values("ano")
    )
    participacao_anual["publica"] = (
        participacao_anual["federal"]
        + participacao_anual["estadual"]
        + participacao_anual["municipal"]
    )

    participacao_anual["nao_informada"] = (
            participacao_anual["total"]
            - participacao_anual["publica"]
            - participacao_anual["privada"]
    )
    _registrar_memoria(
        "Visão Geral | após conversões e agregação participacao_anual"
    )

    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    _registrar_memoria("Visão Geral | após importações do gráfico participação")

    fig_participacao = make_subplots(specs=[[{"secondary_y": True}]])
    _registrar_memoria("Visão Geral | após make_subplots")
    series = [
        ("total", "Total de participantes", "#1f2937"),
        ("publica", "Participantes da rede pública", "#2474a6"),
        ("privada", "Participantes da rede privada", "#e39b38"),
        ("nao_informada", "Dependência administrativa não informada", "#8b929b"),
    ]
    for coluna, nome, cor in series:
        fig_participacao.add_trace(
            go.Scatter(
                x=participacao_anual["ano"],
                y=participacao_anual[coluna],
                name=nome,
                mode="lines+markers",
                line={"width": 2.8, "color": cor},
                marker={"size": 6},
                hovertemplate=f"Ano: %{{x}}<br>{nome}: %{{y:,.0f}}<extra></extra>",
            ),
            secondary_y=False,
        )
        _registrar_memoria(f"Visão Geral | após adicionar série {nome}")



    fig_participacao.update_layout(
        template="plotly_white",
        height=450,
        margin=dict(l=50, r=55, t=70, b=75),
        hovermode="x unified",
        xaxis=dict(title="Ano", dtick=2, showgrid=False),
        legend=dict(title="", orientation="h", y=-0.22),
        title=dict(x=0.02, font=dict(size=18)),
    )
    fig_participacao.update_yaxes(
        title_text="Número de participantes",
        tickformat=",",
        rangemode="tozero",
        secondary_y=False,
    )
    graficos["participacao"] = fig_participacao
    _registrar_memoria("Visão Geral | gráfico participação")

    # Redação: cálculo ponderado e separação por escala
    redacao_anual = _media_estadual_ponderada(
        painel, "media_redacao", "n_validos_redacao"
    )

    redacao_antiga = redacao_anual[redacao_anual["ano"] <= 2008].copy()
    fig_redacao_antiga = px.line(
        redacao_antiga,
        x="ano",
        y="media_estadual",
        markers=True,
        title="Redação — Modelo antigo (1998–2008)",
        labels={"ano": "Ano", "media_estadual": "Nota média"}
    )
    fig_redacao_antiga.update_traces(
        line={"width": 3},
        marker={"size": 7},
        hovertemplate="Ano: %{x}<br>Média estadual: %{y:.2f}<extra></extra>"
    )
    fig_redacao_antiga.update_layout(
        template="plotly_white", height=380,
        margin=dict(l=50, r=30, t=70, b=50),
        xaxis=dict(title="Ano", dtick=1, showgrid=False),
        yaxis=dict(title="Nota média", range=[0, 100]),
        showlegend=False
    )
    graficos["redacao_antiga"] = fig_redacao_antiga
    _registrar_memoria("Visão Geral | gráfico redação antiga")

    redacao_nova = redacao_anual[redacao_anual["ano"] >= 2009].copy()
    fig_redacao_nova = px.line(
        redacao_nova,
        x="ano",
        y="media_estadual",
        markers=True,
        title="Redação — Novo modelo (2009–2025)",
        labels={"ano": "Ano", "media_estadual": "Nota média"}
    )
    fig_redacao_nova.update_traces(
        line={"width": 3},
        marker={"size": 7},
        line_color="darkblue",
        hovertemplate="Ano: %{x}<br>Média estadual: %{y:.2f}<extra></extra>"
    )
    fig_redacao_nova.update_layout(
        template="plotly_white", height=380,
        margin=dict(l=50, r=30, t=70, b=50),
        xaxis=dict(title="Ano", dtick=1, showgrid=False),
        yaxis=dict(title="Nota média", range=[0, 1000]),
        showlegend=False
    )
    graficos["redacao_nova"] = fig_redacao_nova
    _registrar_memoria("Visão Geral | gráfico redação nova")

    # Prova objetiva: modelo antigo
    objetiva_anual = _media_estadual_ponderada(
        painel, "media_objetiva", "n_validos_objetiva", (1998, 2008)
    )

    fig_objetiva = px.line(
        objetiva_anual,
        x="ano",
        y="media_estadual",
        markers=True,
        title="Prova objetiva (1998–2008)",
        labels={"ano": "Ano", "media_estadual": "Nota média"}
    )
    fig_objetiva.update_traces(
        line={"width": 3},
        marker={"size": 7},
        hovertemplate="Ano: %{x}<br>Média estadual: %{y:.2f}<extra></extra>"
    )


    fig_objetiva.update_layout(
        template="plotly_white", height=450,
        margin=dict(l=50, r=30, t=80, b=70),
        hovermode="x unified",
        xaxis=dict(title="Ano", dtick=1, showgrid=False),
        yaxis=dict(title="Nota média estadual", range=[0, 100]),
        showlegend=False
    )
    graficos["objetiva"] = fig_objetiva
    _registrar_memoria("Visão Geral | gráfico prova objetiva")

    # Quatro áreas: novo modelo
    disciplinas = {
        "CN": ("media_cn", "n_validos_cn"),
        "CH": ("media_ch", "n_validos_ch"),
        "LC": ("media_lc", "n_validos_lc"),
        "MT": ("media_mt", "n_validos_mt")
    }
    series_disciplinas = []

    for disciplina, (col_media, col_validos) in disciplinas.items():
        anual = _media_estadual_ponderada(
            painel, col_media, col_validos, (2009, 2025)
        )
        anual["disciplina"] = disciplina
        series_disciplinas.append(anual)

    desempenho_areas = pd.concat(series_disciplinas, ignore_index=True)
    fig_areas = px.line(
        desempenho_areas,
        x="ano",
        y="media_estadual",
        color="disciplina",
        markers=True,
        color_discrete_map={
            "CN": "#2696c8",
            "CH": "#e39b38",
            "LC": "#269b78",
            "MT": "#9a75c9"
        },
        labels={
            "ano": "Ano",
            "media_estadual": "Nota média",
            "disciplina": "Área"
        },
        title="Desempenho por área (2009–2025)"
    )
    fig_areas.update_traces(
        line={"width": 3},
        marker={"size": 7},
        hovertemplate="Ano: %{x}<br>Média estadual: %{y:.2f}<extra></extra>"
    )
    fig_areas.update_layout(
        template="plotly_white", height=450,
        margin=dict(l=50, r=30, t=80, b=70),
        hovermode="x unified",
        xaxis=dict(title="Ano", dtick=1, showgrid=False),
        yaxis=dict(title="Nota média estadual", range=[0, 1000]),
        legend=dict(title="Área de conhecimento", orientation="h", y=-0.22)
    )
    graficos["areas"] = fig_areas
    _registrar_memoria("Visão Geral | gráfico desempenho por área")


    # --------------------------------------------------
    # DESEMPENHO POR DEPENDÊNCIA ADMINISTRATIVA
    # --------------------------------------------------

    _registrar_memoria("Visão Geral | antes da preparação de grupo")
    grupo = dados["grupo"].copy()
    grupo["ano"] = pd.to_numeric(grupo["ano"], errors="coerce")
    grupo["n_validos"] = pd.to_numeric(grupo["n_validos"], errors="coerce")
    grupo["media"] = pd.to_numeric(grupo["media"], errors="coerce")
    grupo["tipo_grupo"] = grupo["tipo_grupo"].astype(str).str.strip().str.upper()
    grupo["grupo"] = grupo["grupo"].astype(str).str.strip().str.upper()
    grupo["disciplina"] = grupo["disciplina"].astype(str).str.strip().str.upper()

    grupo_escola = grupo[
        (grupo["tipo_grupo"] == "ESCOLA")
        & grupo["media"].notna()
        & grupo["n_validos"].notna()
        & (grupo["n_validos"] > 0)
    ].copy()

    redes_publicas = ["MUNICIPAL", "ESTADUAL", "FEDERAL"]
    cores_publico_privado = {
        "Público": "#2474a6",
        "Privado": "#e39b38"
    }
    cores_redes_publicas = {
        "Municipal": "#269b78",
        "Estadual": "#2474a6",
        "Federal": "#9a75c9"
    }

    # Pré-agrega uma única vez por ano, disciplina e grupo escolar.
    # As comparações abaixo reutilizam essa base, evitando percorrer
    # repetidamente todas as linhas de grupo_escola.
    grupo_escola["soma_ponderada"] = grupo_escola["media"] * grupo_escola["n_validos"]
    grupo_agregado = (
        grupo_escola.groupby(["ano", "disciplina", "grupo"], as_index=False)
        .agg(
            soma_ponderada=("soma_ponderada", "sum"),
            notas_validas=("n_validos", "sum")
        )
    )
    _registrar_memoria("Visão Geral | após agregação inicial de grupo escolar")

    def agregar_dependencia(categorias, rotulos, disciplinas_validas, periodo):
        """Agrega médias por ano/disciplina a partir da base pré-agregada."""
        partes = []
        for categoria, rotulo in zip(categorias, rotulos):
            temp = grupo_agregado[
                grupo_agregado["grupo"].isin(categoria)
                & grupo_agregado["disciplina"].isin(disciplinas_validas)
                & grupo_agregado["ano"].between(*periodo)
            ]

            if temp.empty:
                continue

            anual = (
                temp.groupby(["ano", "disciplina"], as_index=False)
                .agg(
                    soma_ponderada=("soma_ponderada", "sum"),
                    notas_validas=("notas_validas", "sum")
                )
            )
            anual["media_estadual"] = anual["soma_ponderada"] / anual["notas_validas"]
            anual["categoria"] = rotulo
            partes.append(anual)

        if not partes:
            return pd.DataFrame(
                columns=["ano", "disciplina", "soma_ponderada", "notas_validas", "media_estadual", "categoria"]
            )
        return pd.concat(partes, ignore_index=True)

    def criar_grafico_dependencia(
        df, titulo, cores, escala, altura=360,
        line_dash=None, line_dash_map=None
    ):
        if df.empty:
            fig = px.line(title=f"{titulo} — sem dados disponíveis")
            fig.update_layout(template="plotly_white", height=altura)
            return fig
        fig = px.line(
            df,
            x="ano",
            y="media_estadual",
            color="categoria",
            line_dash=line_dash,
            line_dash_map=line_dash_map,
            markers=True,
            color_discrete_map=cores,
            labels={
                "ano": "Ano",
                "media_estadual": "Nota média",
                "categoria": "Dependência administrativa"
            },
            title=titulo
        )
        fig.update_traces(
            line={"width": 2.5},
            marker={"size": 6},
            hovertemplate=(
                "Ano: %{x}<br>"
                "Média ponderada: %{y:.2f}<extra></extra>"
            )
        )
        fig.update_layout(
            template="plotly_white",
            height=altura,
            margin=dict(l=45, r=20, t=65, b=65),
            hovermode="x unified",
            xaxis=dict(title="Ano", dtick=1, showgrid=False),
            yaxis=dict(title="Nota média", range=[0, escala]),
            legend=dict(
                title="",
                orientation="h",
                y=-0.28
            )
        )
        return fig

    # Público (municipal + estadual + federal) x privado
    comparacao_pp_antiga = agregar_dependencia(
        [redes_publicas, ["PRIVADA"]],
        ["Público", "Privado"],
        ["REDACAO", "OBJETIVA"],
        (1998, 2008)
    )
    comparacao_pp_nova = agregar_dependencia(
        [redes_publicas, ["PRIVADA"]],
        ["Público", "Privado"],
        ["REDACAO", "CN", "CH", "LC", "MT"],
        (2009, 2025)
    )

    for periodo, dados_periodo, escala in [
        ("antigo", comparacao_pp_antiga, 100),
        ("novo", comparacao_pp_nova, 1000)
    ]:
        red = dados_periodo[dados_periodo["disciplina"] == "REDACAO"]
        prova = dados_periodo[dados_periodo["disciplina"] == "OBJETIVA"] if periodo == "antigo" else pd.DataFrame()
        graficos[f"pp_redacao_{periodo}"] = criar_grafico_dependencia(
            red,
            f"Redação — Público x Privado ({'1998–2008' if periodo == 'antigo' else '2009–2025'})",
            cores_publico_privado,
            escala,
            line_dash="categoria",
            line_dash_map={"Público": "solid", "Privado": "dash"}
        )
        _registrar_memoria(f"Visão Geral | público x privado | redação {periodo}")
        if periodo == "antigo":
            graficos["pp_provas_antigo"] = criar_grafico_dependencia(
                prova,
                "Prova objetiva — Público x Privado (1998–2008)",
                cores_publico_privado,
                escala,
                altura=420,
                line_dash="categoria",
                line_dash_map={"Público": "solid", "Privado": "dash"}
            )

    # Dados das quatro áreas para o seletor interativo Público x Privado.
    dados_pp_areas = comparacao_pp_nova[
        comparacao_pp_nova["disciplina"].isin(["CN", "CH", "LC", "MT"])
    ].copy()
    graficos["pp_areas_dados"] = dados_pp_areas.to_dict("records")
    graficos["pp_areas"] = criar_grafico_area_selecionada(
        graficos["pp_areas_dados"], "CN", "publico_privado"
    )
    _registrar_memoria("Visão Geral | gráficos público x privado")

    # Comparação somente entre as três redes públicas.
    comparacao_publicas_antiga = agregar_dependencia(
        [["MUNICIPAL"], ["ESTADUAL"], ["FEDERAL"]],
        ["Municipal", "Estadual", "Federal"],
        ["REDACAO", "OBJETIVA"],
        (1998, 2008)
    )
    comparacao_publicas_nova = agregar_dependencia(
        [["MUNICIPAL"], ["ESTADUAL"], ["FEDERAL"]],
        ["Municipal", "Estadual", "Federal"],
        ["REDACAO", "CN", "CH", "LC", "MT"],
        (2009, 2025)
    )

    cores_redes_publicas = {
        "Municipal": "#269b78",
        "Estadual": "#2474a6",
        "Federal": "#9a75c9"
    }

    for periodo, dados_periodo, escala in [
        ("antigo", comparacao_publicas_antiga, 100),
        ("novo", comparacao_publicas_nova, 1000)
    ]:
        red = dados_periodo[dados_periodo["disciplina"] == "REDACAO"]
        prova = dados_periodo[dados_periodo["disciplina"] == "OBJETIVA"] if periodo == "antigo" else pd.DataFrame()
        graficos[f"redes_redacao_{periodo}"] = criar_grafico_dependencia(
            red,
            f"Redação — Redes públicas ({'1998–2008' if periodo == 'antigo' else '2009–2025'})",
            cores_redes_publicas,
            escala
        )
        _registrar_memoria(f"Visão Geral | redes públicas | redação {periodo}")
        if periodo == "antigo":
            graficos["redes_provas_antigo"] = criar_grafico_dependencia(
                prova,
                "Prova objetiva — Redes públicas (1998–2008)",
                cores_redes_publicas,
                escala,
                altura=420
            )

    # Dados das quatro áreas para o seletor interativo das redes públicas.
    dados_redes_areas = comparacao_publicas_nova[
        comparacao_publicas_nova["disciplina"].isin(["CN", "CH", "LC", "MT"])
    ].copy()
    graficos["redes_areas_dados"] = dados_redes_areas.to_dict("records")
    graficos["redes_areas"] = criar_grafico_area_selecionada(
        graficos["redes_areas_dados"], "CN", "redes_publicas"
    )
    _registrar_memoria("Visão Geral | gráficos redes públicas")

    _registrar_memoria("Visão Geral | fim de criar_graficos")
    return graficos
