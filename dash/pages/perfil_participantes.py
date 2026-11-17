#pagina_participantes.py

"""Página de perfil sociodemográfico dos participantes do ENEM."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Input, Output, State, dcc, html
from dash_utils.ufs import nome_uf
from dash_utils.perf import etapa, medir_callback

from utils.eda import MAPA_FAIXA_5, ORDEM_FAIXAS


DISCIPLINAS = {
    "Redação": "REDACAO",
    "Ciências da Natureza": "CN",
    "Ciências Humanas": "CH",
    "Linguagens": "LC",
    "Matemática": "MT",
    "Prova objetiva (1998–2008)": "OBJETIVA",
}

CORES_SEXO = {
    "FEMININO": "#d95f9f",
    "MASCULINO": "#2878b5",
}


def _codigo_municipio(serie):
    return (
        serie.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(7)
    )


def _figura_vazia(mensagem, altura=380):
    fig = go.Figure()
    fig.add_annotation(
        text=mensagem,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 14, "color": "#64748b"},
    )
    fig.update_layout(
        template="plotly_white",
        height=altura,
        margin={"l": 35, "r": 25, "t": 65, "b": 45},
    )
    return fig


def _card(titulo, valor, subtitulo=""):
    return html.Div(
        [
            html.Div(titulo, style={"fontSize": "12px", "color": "#64748b"}),
            html.Div(
                valor,
                style={
                    "fontSize": "25px",
                    "fontWeight": "700",
                    "color": "#0f172a",
                    "marginTop": "7px",
                },
            ),
            html.Div(
                subtitulo,
                style={"fontSize": "10px", "color": "#94a3b8", "marginTop": "4px"},
            ),
        ],
        style={
            "background": "white",
            "border": "1px solid #e2e8f0",
            "borderRadius": "8px",
            "padding": "14px",
            "minWidth": "0",
        },
    )


def _formatar_numero(valor):
    if pd.isna(valor):
        return "—"
    return f"{valor:,.0f}".replace(",", ".")


def _formatar_percentual(valor):
    if pd.isna(valor):
        return "—"
    return f"{valor:.1f}%".replace(".", ",")


def _preparar_painel(painel):
    df = painel.copy()
    obrigatorias = {"ano", "CO_MUNICIPIO_TERRITORIO", "n_participantes"}
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(
            "O painel de Consumo não contém as colunas necessárias "
            f"para a página de perfil: {sorted(faltantes)}"
        )

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["codigo"] = _codigo_municipio(df["CO_MUNICIPIO_TERRITORIO"])

    for coluna in [
        "n_participantes",
        "n_masculino",
        "n_feminino",
        "n_faixa_etaria_informada",
    ]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    return df.dropna(subset=["ano"]).copy()


def _preparar_faixa(faixa):
    df = faixa.copy()
    obrigatorias = {
        "ano",
        "CO_MUNICIPIO_TERRITORIO",
        "TP_FAIXA_ETARIA",
        "n_participantes",
    }
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(
            "O produto faixa_etaria_municipal não contém as colunas "
            f"necessárias: {sorted(faltantes)}"
        )

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["codigo"] = _codigo_municipio(df["CO_MUNICIPIO_TERRITORIO"])
    df["faixa_codigo"] = pd.to_numeric(df["TP_FAIXA_ETARIA"], errors="coerce")
    df["faixa"] = df["faixa_codigo"].map(MAPA_FAIXA_5)
    df["n_participantes"] = pd.to_numeric(
        df["n_participantes"], errors="coerce"
    )
    df = df.dropna(subset=["ano", "faixa", "n_participantes"]).copy()
    df["faixa"] = pd.Categorical(
        df["faixa"], categories=ORDEM_FAIXAS, ordered=True
    )
    return df


def _preparar_grupo(grupo):
    df = grupo.copy()
    obrigatorias = {
        "ano",
        "CO_MUNICIPIO_TERRITORIO",
        "tipo_grupo",
        "grupo",
        "disciplina",
        "media",
        "n_validos",
    }
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(
            "O produto desempenho_grupos_municipal não contém as colunas "
            f"necessárias: {sorted(faltantes)}"
        )

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["codigo"] = _codigo_municipio(df["CO_MUNICIPIO_TERRITORIO"])
    df["tipo_grupo"] = df["tipo_grupo"].astype("string").str.upper().str.strip()
    df["grupo"] = df["grupo"].astype("string").str.upper().str.strip()
    df["disciplina"] = df["disciplina"].astype("string").str.upper().str.strip()
    df["media"] = pd.to_numeric(df["media"], errors="coerce")
    df["n_validos"] = pd.to_numeric(df["n_validos"], errors="coerce")
    return df.dropna(
        subset=["ano", "media", "n_validos"]
    ).loc[lambda x: x["n_validos"] > 0].copy()


def _preparar_dsp(dsp):
    """Prepara o produto de desempenho cruzado por sexo e faixa etária."""
    df = dsp.copy()
    obrigatorias = {
        "ano",
        "CO_MUNICIPIO_TERRITORIO",
        "sexo",
        "faixa_etaria",
        "disciplina",
        "n_participantes",
        "n_validos",
        "media",
        "std",
    }
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(
            "O produto desempenho_sexo_faixa_etaria_municipal não contém "
            f"as colunas necessárias: {sorted(faltantes)}"
        )

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["codigo"] = _codigo_municipio(df["CO_MUNICIPIO_TERRITORIO"])
    df["sexo"] = df["sexo"].astype("string").str.upper().str.strip()
    df["faixa_codigo"] = pd.to_numeric(df["faixa_etaria"], errors="coerce")
    df["faixa"] = df["faixa_codigo"].map(MAPA_FAIXA_5)
    df["disciplina"] = df["disciplina"].astype("string").str.upper().str.strip()

    for coluna in ["n_participantes", "n_validos", "media", "std"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    return df.dropna(
        subset=["ano", "sexo", "faixa", "disciplina", "n_participantes"]
    ).copy()


def _agregar_piramide_sexo_faixa(dsp, ano):
    """Conta participantes por sexo e faixa, usando REDACAO uma única vez."""
    if dsp.empty:
        return pd.DataFrame()

    df = dsp[
        (dsp["ano"] == int(ano))
        & (dsp["disciplina"] == "REDACAO")
        & (dsp["sexo"].isin(["FEMININO", "MASCULINO"]))
    ].copy()
    if df.empty:
        return df

    resultado = (
        df.groupby(["sexo", "faixa"], observed=True, as_index=False)
        ["n_participantes"].sum()
    )
    resultado["valor_piramide"] = np.where(
        resultado["sexo"] == "FEMININO",
        -resultado["n_participantes"],
        resultado["n_participantes"],
    )
    resultado["faixa"] = pd.Categorical(
        resultado["faixa"], categories=ORDEM_FAIXAS, ordered=True
    )
    return resultado.sort_values("faixa")


def _agregar_media_ic95(df, chaves):
    """
    Agrega médias ponderadas e estima IC95% da média.

    A variância individual combinada reúne a variância intramunicipal
    (std²) e a variabilidade entre médias municipais. Pressupõe std
    amostral e participantes independentes; usa aproximação normal (1,96).
    """
    base = df.dropna(subset=["media", "n_validos"]).copy()
    base = base[base["n_validos"] > 0]
    base["std"] = pd.to_numeric(base["std"], errors="coerce")
    if base.empty:
        return pd.DataFrame()

    base["soma_ponderada"] = base["media"] * base["n_validos"]
    base["ss_intra"] = np.where(
        (base["n_validos"] > 1) & base["std"].notna(),
        (base["n_validos"] - 1) * base["std"].pow(2),
        0.0,
    )

    resultado = (
        base.groupby(chaves, observed=True, as_index=False)
        .agg(
            soma_ponderada=("soma_ponderada", "sum"),
            n_validos=("n_validos", "sum"),
            ss_intra=("ss_intra", "sum"),
        )
    )
    resultado["media"] = resultado["soma_ponderada"] / resultado["n_validos"]

    base = base.merge(
        resultado[chaves + ["media"]].rename(columns={"media": "media_agregada"}),
        on=chaves,
        how="left",
    )
    base["ss_entre"] = (
        base["n_validos"] * (base["media"] - base["media_agregada"]).pow(2)
    )
    ss_entre = base.groupby(chaves, observed=True, as_index=False)["ss_entre"].sum()
    resultado = resultado.merge(ss_entre, on=chaves, how="left")

    graus_liberdade = resultado["n_validos"] - 1
    resultado["variancia_combinada"] = (
        (resultado["ss_intra"] + resultado["ss_entre"])
        / graus_liberdade.where(graus_liberdade > 0)
    )
    resultado["std_combinado"] = np.sqrt(resultado["variancia_combinada"])
    resultado["erro_ic95"] = 1.96 * resultado["std_combinado"] / np.sqrt(
        resultado["n_validos"]
    )
    resultado["ic95_inferior"] = resultado["media"] - resultado["erro_ic95"]
    resultado["ic95_superior"] = resultado["media"] + resultado["erro_ic95"]
    return resultado


def _agregar_desempenho_sexo_faixa(dsp, disciplina):
    """Média ponderada e IC95% por ano, sexo e faixa etária."""
    if dsp.empty:
        return pd.DataFrame()
    df = dsp[
        (dsp["disciplina"] == disciplina)
        & dsp["sexo"].isin(["FEMININO", "MASCULINO"])
    ].copy()
    resultado = _agregar_media_ic95(df, ["ano", "sexo", "faixa"])
    if resultado.empty:
        return resultado
    resultado["faixa"] = pd.Categorical(
        resultado["faixa"], categories=ORDEM_FAIXAS, ordered=True
    )
    return resultado.sort_values(["ano", "faixa", "sexo"])


def _agregar_desempenho_sexo_dp(dsp, disciplina):
    """Média ponderada e IC95% por ano e sexo."""
    if dsp.empty:
        return pd.DataFrame()
    df = dsp[
        (dsp["disciplina"] == disciplina)
        & dsp["sexo"].isin(["FEMININO", "MASCULINO"])
    ].copy()
    return _agregar_media_ic95(df, ["ano", "sexo"])


def _agregar_sexo(painel):
    colunas = {"n_masculino", "n_feminino"}
    if not colunas.issubset(painel.columns):
        return pd.DataFrame()

    df = (
        painel.groupby("ano", as_index=False)[
            ["n_participantes", "n_masculino", "n_feminino"]
        ]
        .sum(min_count=1)
        .sort_values("ano")
    )
    denominador = df["n_masculino"] + df["n_feminino"]
    df["pct_masculino"] = 100 * df["n_masculino"] / denominador.where(denominador > 0)
    df["pct_feminino"] = 100 * df["n_feminino"] / denominador.where(denominador > 0)
    return df


def _agregar_faixa(faixa):
    if faixa.empty:
        return pd.DataFrame()
    resultado = (
        faixa.groupby(["ano", "faixa"], observed=True, as_index=False)["n_participantes"]
        .sum()
    )
    resultado["faixa"] = pd.Categorical(
        resultado["faixa"], categories=ORDEM_FAIXAS, ordered=True
    )
    return resultado.sort_values(["ano", "faixa"])


def _agregar_desempenho(grupo, tipo_grupo, disciplina):
    if grupo.empty:
        return pd.DataFrame()

    df = grupo[
        (grupo["tipo_grupo"] == tipo_grupo)
        & (grupo["disciplina"] == disciplina)
    ].copy()
    if df.empty:
        return df

    df["soma_ponderada"] = df["media"] * df["n_validos"]
    resultado = (
        df.groupby(["ano", "grupo"], as_index=False)
        .agg(
            soma_ponderada=("soma_ponderada", "sum"),
            n_validos=("n_validos", "sum"),
        )
    )
    resultado["media"] = resultado["soma_ponderada"] / resultado["n_validos"]
    return resultado.sort_values(["ano", "grupo"])


def _rotulo_faixa(codigo):
    if pd.isna(codigo):
        return None
    return MAPA_FAIXA_5.get(int(codigo))


def _agregar_desempenho_faixa(grupo, disciplina):
    df = _agregar_desempenho(grupo, "FAIXA_ETARIA", disciplina)
    if df.empty:
        return df

    df["faixa_codigo"] = pd.to_numeric(df["grupo"], errors="coerce")
    df["faixa"] = df["faixa_codigo"].map(MAPA_FAIXA_5)
    df = df.dropna(subset=["faixa", "n_validos"]).copy()
    if df.empty:
        return df

    df["soma_ponderada"] = df["media"] * df["n_validos"]
    resultado = (
        df.groupby(["ano", "faixa"], observed=True, as_index=False)
        .agg(
            soma_ponderada=("soma_ponderada", "sum"),
            n_validos=("n_validos", "sum"),
        )
    )
    resultado["media"] = resultado["soma_ponderada"] / resultado["n_validos"]
    resultado["faixa"] = pd.Categorical(
        resultado["faixa"], categories=ORDEM_FAIXAS, ordered=True
    )
    return resultado.sort_values(["ano", "faixa"])


def _figura_composicao_sexo(painel, agregado=None):
    df = agregado if agregado is not None else _agregar_sexo(painel)
    if df.empty or not df[["pct_masculino", "pct_feminino"]].notna().any().any():
        return _figura_vazia(
            "Distribuição por sexo indisponível na base para os anos selecionados."
        )

    fig = go.Figure()
    for grupo, coluna in [
        ("FEMININO", "pct_feminino"),
        ("MASCULINO", "pct_masculino"),
    ]:
        fig.add_trace(
            go.Scatter(
                x=df["ano"],
                y=df[coluna],
                mode="lines+markers",
                name=grupo.title(),
                line={"color": CORES_SEXO[grupo], "width": 2.5},
                hovertemplate="%{x}: %{y:.1f}%<extra>" + grupo.title() + "</extra>",
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=390,
        title="Composição dos participantes por sexo",
        xaxis_title="Ano",
        yaxis_title="Participação (%)",
        yaxis={"rangemode": "tozero"},
        legend_title="Sexo",
        margin={"l": 45, "r": 20, "t": 65, "b": 45},
    )
    return fig


def _figura_evolucao_faixa(faixa, agregado=None):
    df = agregado if agregado is not None else _agregar_faixa(faixa)
    if df.empty:
        return _figura_vazia("Não há distribuição etária disponível.")

    total_ano = df.groupby("ano")["n_participantes"].transform("sum")
    df["percentual"] = 100 * df["n_participantes"] / total_ano.where(total_ano > 0)
    fig = px.area(
        df,
        x="ano",
        y="percentual",
        color="faixa",
        labels={
            "ano": "Ano",
            "percentual": "Participação (%)",
            "faixa": "Faixa etária",
        },
        title="Mudança na composição etária ao longo do tempo",
    )
    fig.update_layout(
        template="plotly_white",
        height=430,
        yaxis_title="Participação (%)",
        margin={"l": 45, "r": 20, "t": 65, "b": 45},
    )
    fig.update_yaxes(ticksuffix="%")
    return fig


def _figura_desempenho_sexo(dsp, disciplina, agregado=None):
    df = agregado if agregado is not None else _agregar_desempenho_sexo_dp(dsp, disciplina)
    if df.empty:
        return _figura_vazia(
            "Desempenho por sexo e IC95% indisponíveis."
        )

    fig = go.Figure()
    for sexo in ["FEMININO", "MASCULINO"]:
        parte = df[df["sexo"] == sexo].sort_values("ano")
        if parte.empty:
            continue
        cor = CORES_SEXO.get(sexo)
        preenchimento = (
            "rgba(217,95,159,0.18)"
            if sexo == "FEMININO"
            else "rgba(40,120,181,0.18)"
        )
        fig.add_trace(go.Scatter(
            x=parte["ano"], y=parte["ic95_superior"],
            mode="lines", line={"width": 0}, showlegend=False,
            hoverinfo="skip", legendgroup=sexo,
        ))
        fig.add_trace(go.Scatter(
            x=parte["ano"], y=parte["ic95_inferior"],
            mode="lines", line={"width": 0}, fill="tonexty",
            fillcolor=preenchimento, showlegend=False,
            hoverinfo="skip", legendgroup=sexo,
        ))
        fig.add_trace(go.Scatter(
            x=parte["ano"], y=parte["media"],
            mode="lines+markers", name=sexo.title(),
            line={"color": cor, "width": 2.5},
            marker={"color": cor},
            customdata=np.column_stack([
                parte["n_validos"], parte["ic95_inferior"],
                parte["ic95_superior"],
            ]),
            hovertemplate=(
                "%{x}: %{y:.2f}<br>"
                "IC95%: %{customdata[1]:.2f} a %{customdata[2]:.2f}<br>"
                "N válido: %{customdata[0]:,.0f}"
                "<extra>" + sexo.title() + "</extra>"
            ),
        ))

    fig.update_layout(
        template="plotly_white", height=410,
        title=f"Evolução do desempenho por sexo — {disciplina}",
        xaxis_title="Ano", yaxis_title="Nota média",
        legend_title="Sexo",
        margin={"l": 45, "r": 20, "t": 65, "b": 45},
    )
    return fig


def _figura_distribuicao_faixa(faixa, ano, agregado=None):
    df = agregado if agregado is not None else _agregar_faixa(faixa)
    if df.empty:
        return _figura_vazia("Não há distribuição etária disponível.")

    df = df[df["ano"] == int(ano)].copy()
    if df.empty:
        return _figura_vazia(f"Não há distribuição etária para {ano}.")

    fig = px.bar(
        df.sort_values("faixa"),
        x="faixa",
        y="n_participantes",
        text="n_participantes",
        labels={
            "faixa": "Faixa etária",
            "n_participantes": "Participantes",
        },
        title=f"Distribuição dos participantes por faixa etária — {ano}",
    )
    fig.update_traces(
        marker_color="#3984b8",
        texttemplate="%{text:,.0f}",
        textposition="outside",
        hovertemplate="%{x}<br>Participantes: %{y:,.0f}<extra></extra>",
    )
    fig.update_layout(
        template="plotly_white",
        height=410,
        xaxis_title="Faixa etária agrupada",
        yaxis_title="Participantes",
        margin={"l": 45, "r": 20, "t": 65, "b": 65},
    )
    return fig


def _figura_desempenho_faixa(grupo, disciplina, ano):
    df = _agregar_desempenho_faixa(grupo, disciplina)
    if df.empty:
        return _figura_vazia(
            "Desempenho por faixa etária indisponível para esta disciplina."
        )

    df = df[df["ano"] == int(ano)].copy()
    if df.empty:
        return _figura_vazia(f"Não há desempenho por faixa etária para {ano}.")

    fig = px.bar(
        df,
        x="faixa",
        y="media",
        custom_data=["n_validos"],
        labels={"faixa": "Faixa etária", "media": "Nota média"},
        title=f"Desempenho por faixa etária — {disciplina} — {ano}",
    )
    fig.update_traces(
        marker_color="#20a486",
        hovertemplate=(
            "%{x}<br>Média: %{y:.2f}<br>"
            "N válido: %{customdata[0]:,.0f}<extra></extra>"
        ),
    )
    fig.update_layout(
        template="plotly_white",
        height=410,
        xaxis_title="Faixa etária agrupada",
        yaxis_title="Nota média",
        margin={"l": 45, "r": 20, "t": 65, "b": 65},
    )
    return fig


def _figura_piramide_sexo_faixa(dsp, ano):
    df = _agregar_piramide_sexo_faixa(dsp, ano)
    if df.empty:
        return _figura_vazia(
            "Não há dados cruzados de sexo e faixa etária para este ano."
        )

    fig = go.Figure()
    for sexo in ["FEMININO", "MASCULINO"]:
        parte = df[df["sexo"] == sexo].sort_values("faixa")
        if parte.empty:
            continue
        fig.add_trace(
            go.Bar(
                y=parte["faixa"].astype(str),
                x=parte["valor_piramide"],
                orientation="h",
                name=sexo.title(),
                marker_color=CORES_SEXO[sexo],
                customdata=parte["n_participantes"],
                hovertemplate=(
                    "%{y}<br>Participantes: %{customdata:,.0f}"
                    "<extra>" + sexo.title() + "</extra>"
                ),
            )
        )

    limite = float(df["n_participantes"].max()) * 1.15
    fig.update_layout(
        template="plotly_white",
        height=440,
        title=f"Pirâmide etária por sexo — {ano}",
        xaxis_title="Participantes",
        yaxis_title="Faixa etária",
        barmode="relative",
        bargap=0.12,
        margin={"l": 45, "r": 25, "t": 65, "b": 50},
        legend_title="Sexo",
    )
    fig.update_xaxes(
        range=[-limite, limite],
        tickvals=[-limite, -limite / 2, 0, limite / 2, limite],
        ticktext=[
            _formatar_numero(limite),
            _formatar_numero(limite / 2),
            "0",
            _formatar_numero(limite / 2),
            _formatar_numero(limite),
        ],
    )
    return fig


def _figura_desempenho_cruzado(dsp, disciplina, ano, agregado=None):
    df = agregado if agregado is not None else _agregar_desempenho_sexo_faixa(dsp, disciplina)
    if df.empty:
        return _figura_vazia(
            "Desempenho cruzado por sexo e faixa etária indisponível."
        )

    df = df[df["ano"] == int(ano)].copy()
    if df.empty:
        return _figura_vazia(
            f"Não há desempenho cruzado para {disciplina} em {ano}."
        )

    fig = px.bar(
        df,
        x="faixa",
        y="media",
        color="sexo",
        barmode="group",
        custom_data=["n_validos", "ic95_inferior", "ic95_superior"],
        error_y="erro_ic95",
        color_discrete_map=CORES_SEXO,
        category_orders={"faixa": ORDEM_FAIXAS},
        labels={
            "faixa": "Faixa etária",
            "media": "Nota média",
            "sexo": "Sexo",
        },
        title=f"Desempenho por sexo e faixa etária — {disciplina} — {ano}",
    )
    fig.update_traces(
        hovertemplate=(
            "%{x}<br>Nota média: %{y:.2f}<br>"
            "IC95%: %{customdata[1]:.2f} a %{customdata[2]:.2f}<br>"
            "Notas válidas: %{customdata[0]:,.0f}<extra>%{fullData.name}</extra>"
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=440,
        xaxis_title="Faixa etária",
        yaxis_title="Nota média",
        legend_title="Sexo",
        margin={"l": 45, "r": 25, "t": 65, "b": 65},
    )
    return fig


def _sigla_uf_dados(dados):
    return dados["uf"]

def criar_layout_perfil(dados):
    painel = _preparar_painel(dados["painel"])
    anos = sorted(painel["ano"].dropna().astype(int).unique().tolist())
    if not anos:
        raise ValueError("Não há anos disponíveis no painel de participantes.")

    grupo = _preparar_grupo(dados["grupo"])
    disciplinas_disponiveis = set(grupo["disciplina"].dropna().unique())
    opcoes_disciplina = [
        {"label": nome, "value": codigo}
        for nome, codigo in DISCIPLINAS.items()
        if codigo in disciplinas_disponiveis
    ]
    if not opcoes_disciplina:
        opcoes_disciplina = [{"label": "Redação", "value": "REDACAO"}]

    return html.Div(
        [
            html.H2(
                f"Perfil dos participantes — ENEM em {nome_uf(_sigla_uf_dados(dados))}",
                style={"color": "#0f172a", "marginBottom": "6px"},
            ),
            html.P(
                "Evolução do perfil por sexo e faixa etária e sua relação "
                "com o desempenho nas avaliações.",
                style={"color": "#64748b", "marginTop": "0"},
            ),

            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                "Ano de referência",
                                style={"fontWeight": "600"},
                            ),
                            dcc.Dropdown(
                                id="perfil-ano",
                                options=[
                                    {"label": str(ano), "value": ano}
                                    for ano in anos
                                ],
                                value=anos[-4],
                                clearable=False,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Avaliação",
                                style={"fontWeight": "600"},
                            ),
                            dcc.Dropdown(
                                id="perfil-disciplina",
                                options=opcoes_disciplina,
                                value=opcoes_disciplina[0]["value"],
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
                id="perfil-kpis",
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, minmax(0, 1fr))",
                    "gap": "12px",
                    "marginBottom": "22px",
                },
            ),

            html.H3("1. Evolução do perfil dos participantes"),
            html.Div(
                [
                    dcc.Graph(
                        id="perfil-sexo-evolucao",
                        config={"responsive": True},
                    ),
                    dcc.Graph(
                        id="perfil-faixa-evolucao",
                        config={"responsive": True},
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                    "gap": "14px",
                },
            ),

            html.H3(
                "2. Gênero e desempenho",
                style={"marginTop": "26px"},
            ),
            dcc.Graph(
                id="perfil-desempenho-sexo",
                config={"responsive": True},
            ),

            html.H3(
                "3. Faixa etária e desempenho",
                style={"marginTop": "26px"},
            ),
            html.Div(
                [
                    dcc.Graph(
                        id="perfil-distribuicao-faixa",
                        config={"responsive": True},
                    ),
                    dcc.Graph(
                        id="perfil-piramide-sexo-faixa",
                        config={"responsive": True},
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                    "gap": "14px",
                },
            ),

            html.H3(
                "4. Desempenho cruzado por sexo e faixa etária",
                style={"marginTop": "26px"},
            ),
            dcc.Graph(
                id="perfil-desempenho-cruzado",
                config={"responsive": True},
            ),

            html.Div(
                [
                    html.Strong("Notas metodológicas"),
                    html.Ul(
                        [
                            html.Li(
                                "A distribuição por sexo utiliza as contagens "
                                "demográficas do painel; os percentuais são "
                                "calculados sobre os registros com sexo informado."
                            ),
                            html.Li(
                                "As médias de desempenho por grupo são ponderadas "
                                "pelo número de notas válidas (n_validos)."
                            ),
                            html.Li(
                                "O produto de desempenho por sexo e faixa etária "
                                "tem disponibilidade histórica até 2023; anos sem "
                                "dados não são interpolados."
                            ),
                            html.Li(
                                "TP_FAIXA_ETARIA contém índices, não idades. "
                                "Os índices são agrupados nas cinco categorias "
                                "definidas em utils.eda.MAPA_FAIXA_5."
                            ),
                            html.Li(
                                "A pirâmide utiliza a contagem do produto cruzado "
                                "filtrada para REDACAO, evitando repetir participantes "
                                "por disciplina."
                            ),
                            html.Li(
                                "O desempenho cruzado utiliza diretamente sexo × "
                                "faixa etária e médias ponderadas por notas válidas."
                            ),
                            html.Li(
                                "As bandas do gráfico temporal e as barras de erro do "
                                "gráfico cruzado representam intervalos de confiança de 95% (IC95%) "
                                "da média, estimados por aproximação normal."
                            ),
                            html.Li(
                                "A variância usada no IC95% combina a dispersão intramunicipal "
                                "(std) e a variabilidade entre médias municipais, "
                                "ponderadas por n_validos. Pressupõe std amostral e "
                                "independência entre participantes."
                            ),
                            html.Li(
                                "O IC95% expressa a incerteza da média estimada; não representa "
                                "a dispersão das notas individuais nem os valores mínimo "
                                "e máximo observados. A sobreposição visual dos intervalos, "
                                "isoladamente, não constitui teste de diferença entre grupos."
                            ),
                        ],
                        style={"paddingLeft": "20px", "marginBottom": "0"},
                    ),
                ],
                style={
                    "fontSize": "12px",
                    "color": "#64748b",
                    "background": "white",
                    "border": "1px solid #e2e8f0",
                    "borderRadius": "8px",
                    "padding": "14px",
                    "marginTop": "22px",
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


def registrar_callbacks_perfil(app, carregar_dados):
    @app.callback(
        Output("perfil-kpis", "children"),
        Output("perfil-sexo-evolucao", "figure"),
        Output("perfil-faixa-evolucao", "figure"),
        Output("perfil-desempenho-sexo", "figure"),
        Output("perfil-distribuicao-faixa", "figure"),
        Output("perfil-piramide-sexo-faixa", "figure"),
        Output("perfil-desempenho-cruzado", "figure"),
        State("seletor-referencia-territorial", "value"),
        State("seletor-uf", "value"),
        Input("perfil-ano", "value"),
        Input("perfil-disciplina", "value"),
    )
    @medir_callback("perfil · atualizar_perfil (7 saídas)")
    def atualizar_perfil(referencia, uf, ano, disciplina):
        dados = carregar_dados(uf, referencia=referencia)
        with etapa("perfil: preparar 4 tabelas (copy + to_numeric + códigos)"):
            painel = _preparar_painel(dados["painel"])
            faixa = _preparar_faixa(dados["faixa"])
            grupo = _preparar_grupo(dados["grupo"])
            dsp = _preparar_dsp(dados["dsp"])

        anos_disponiveis = painel["ano"].dropna().astype(int)
        if ano is None or int(ano) not in set(anos_disponiveis):
            ano = int(anos_disponiveis.max())

        atual = painel[painel["ano"] == int(ano)]
        total = (
            pd.to_numeric(atual["n_participantes"], errors="coerce").sum()
            if not atual.empty
            else np.nan
        )

        if {"n_masculino", "n_feminino"}.issubset(atual.columns):
            masculino = pd.to_numeric(
                atual["n_masculino"], errors="coerce"
            ).sum(min_count=1)
            feminino = pd.to_numeric(
                atual["n_feminino"], errors="coerce"
            ).sum(min_count=1)
            denom_sexo = masculino + feminino
            pct_feminino = (
                100 * feminino / denom_sexo
                if pd.notna(denom_sexo) and denom_sexo > 0
                else np.nan
            )
        else:
            masculino = feminino = pct_feminino = np.nan

        if "n_faixa_etaria_informada" in atual.columns:
            n_idade = pd.to_numeric(
                atual["n_faixa_etaria_informada"], errors="coerce"
            ).sum(min_count=1)
        else:
            n_idade = np.nan
        cobertura_idade = (
            100 * n_idade / total
            if pd.notna(n_idade) and pd.notna(total) and total > 0
            else np.nan
        )

        kpis = [
            _card("Participantes", _formatar_numero(total), f"Ano {ano}"),
            _card("Participantes do sexo feminino", _formatar_numero(feminino), "Sexo informado"),
            _card("Participantes do sexo masculino", _formatar_numero(masculino), "Sexo informado"),
            _card("Idade informada", _formatar_percentual(cobertura_idade), "Cobertura sobre participantes"),
        ]

        # Agregações compartilhadas entre gráficos são calculadas uma única vez.
        with etapa("perfil: agregações"):
            sexo_agregado = _agregar_sexo(painel)
            faixa_agregada = _agregar_faixa(faixa)
            desempenho_sexo_agregado = _agregar_desempenho_sexo_dp(dsp, disciplina)
            desempenho_cruzado_agregado = _agregar_desempenho_sexo_faixa(dsp, disciplina)

        return (
            kpis,
            _figura_composicao_sexo(painel, sexo_agregado),
            _figura_evolucao_faixa(faixa, faixa_agregada),
            _figura_desempenho_sexo(dsp, disciplina, desempenho_sexo_agregado),
            _figura_distribuicao_faixa(faixa, ano, faixa_agregada),
            _figura_piramide_sexo_faixa(dsp, ano),
            _figura_desempenho_cruzado(
                dsp, disciplina, ano, desempenho_cruzado_agregado
            ),
        )
