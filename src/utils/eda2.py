"""
eda2.py
Funções reutilizáveis de auditoria e análise exploratória do Projeto ENEM.

Este módulo inicia o Eixo 1 (participação) e será ampliado progressivamente
durante a construção dos sete notebooks analíticos.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


CHAVES_MUNICIPIO_ANO = [
    "ano",
    "CO_MUNICIPIO_TERRITORIO",
]


def validar_colunas(df: pd.DataFrame, colunas: list[str], nome: str = "DataFrame") -> None:
    """Verifica se as colunas necessárias estão presentes."""
    ausentes = [col for col in colunas if col not in df.columns]
    if ausentes:
        raise ValueError(f"{nome}: colunas ausentes: {ausentes}")


def filtrar_referencia(
    df: pd.DataFrame,
    referencia: str = "ESC",
) -> pd.DataFrame:
    """Retorna somente a referência territorial solicitada, quando aplicável."""
    if "TIPO_REFERENCIA_TERRITORIAL" not in df.columns:
        return df.copy()
    return df.loc[
        df["TIPO_REFERENCIA_TERRITORIAL"].astype("string").str.upper().eq(referencia.upper())
    ].copy()


def auditar_painel_participacao(
    df: pd.DataFrame,
    uf: str | None = None,
    referencia: str = "ESC",
) -> dict:
    """
    Audita a estrutura básica do painel para análises de participação.

    Retorna tabelas de duplicidades, cobertura anual, cobertura municipal,
    consistência entre contagens e totais anuais. Não altera o DataFrame original.
    """
    obrigatorias = [
        "ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO",
        "n_participantes",
    ]
    validar_colunas(df, obrigatorias, "painel")

    dados = filtrar_referencia(df, referencia)
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados["n_participantes"] = pd.to_numeric(
        dados["n_participantes"], errors="coerce"
    )

    duplicidades = (
        dados.loc[dados.duplicated(CHAVES_MUNICIPIO_ANO, keep=False)]
        .sort_values(CHAVES_MUNICIPIO_ANO)
        if all(c in dados.columns for c in CHAVES_MUNICIPIO_ANO)
        else pd.DataFrame()
    )

    cobertura_anual = (
        dados.groupby("ano", dropna=False)
        .agg(
            n_registros=("CO_MUNICIPIO_TERRITORIO", "size"),
            n_municipios=("CO_MUNICIPIO_TERRITORIO", "nunique"),
            participantes=("n_participantes", "sum"),
            participantes_nulos=("n_participantes", lambda s: s.isna().sum()),
        )
        .reset_index()
        .sort_values("ano")
    )

    cobertura_municipal = (
        dados.groupby(
            ["CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO"],
            dropna=False,
        )
        .agg(
            ano_inicial=("ano", "min"),
            ano_final=("ano", "max"),
            n_anos=("ano", "nunique"),
            n_registros=("ano", "size"),
        )
        .reset_index()
        .sort_values("n_anos", ascending=False)
    )

    comparacao_contagens = pd.DataFrame()
    if "n_registros_escola" in dados.columns:
        comparacao_contagens = dados[
            ["ano", "CO_MUNICIPIO_TERRITORIO", "n_participantes", "n_registros_escola"]
        ].copy()
        comparacao_contagens["diferenca"] = (
            pd.to_numeric(comparacao_contagens["n_participantes"], errors="coerce")
            - pd.to_numeric(comparacao_contagens["n_registros_escola"], errors="coerce")
        )

    anos = sorted(dados["ano"].dropna().astype(int).unique().tolist())
    anos_esperados = list(range(min(anos), max(anos) + 1)) if anos else []
    anos_ausentes = sorted(set(anos_esperados) - set(anos))

    resumo = {
        "uf": uf,
        "referencia": referencia,
        "shape_original": df.shape,
        "shape_filtrado": dados.shape,
        "anos_encontrados": anos,
        "anos_ausentes_no_intervalo": anos_ausentes,
        "n_municipios": dados["CO_MUNICIPIO_TERRITORIO"].nunique(),
        "n_linhas_duplicadas_chave": len(duplicidades),
        "n_participantes_nulos": int(dados["n_participantes"].isna().sum()),
        "soma_anual": cobertura_anual,
        "cobertura_municipal": cobertura_municipal,
        "duplicidades": duplicidades,
        "comparacao_contagens": comparacao_contagens,
        "dados": dados,
    }
    return resumo


def calcular_participacao_anual(
    df: pd.DataFrame,
    coluna_valor: str = "n_participantes",
) -> pd.DataFrame:
    """Agrega participantes por ano, somando contagens municipais."""
    validar_colunas(df, ["ano", coluna_valor], "DataFrame")
    dados = df.copy()
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados[coluna_valor] = pd.to_numeric(dados[coluna_valor], errors="coerce")
    resultado = (
        dados.groupby("ano", as_index=False)
        .agg(
            participantes=(coluna_valor, "sum"),
            n_registros=(coluna_valor, "count"),
        )
        .sort_values("ano")
    )
    resultado["variacao_absoluta"] = resultado["participantes"].diff()
    resultado["variacao_percentual"] = (
        resultado["participantes"].pct_change(fill_method=None) * 100
    )
    resultado["crescimento_acumulado_pct"] = (
        resultado["participantes"] / resultado["participantes"].iloc[0] - 1
    ) * 100 if len(resultado) and resultado["participantes"].iloc[0] != 0 else np.nan
    resultado["cagr_pct"] = np.nan
    if len(resultado) > 1:
        primeiro = resultado["participantes"].iloc[0]
        ultimo = resultado["participantes"].iloc[-1]
        intervalo = resultado["ano"].iloc[-1] - resultado["ano"].iloc[0]
        if primeiro > 0 and ultimo >= 0 and intervalo > 0:
            resultado.loc[resultado.index[-1], "cagr_pct"] = (
                (ultimo / primeiro) ** (1 / intervalo) - 1
            ) * 100
    return resultado.reset_index(drop=True)


def calcular_variacao_participacao(
    df: pd.DataFrame,
    coluna_valor: str = "n_participantes",
) -> pd.DataFrame:
    """Calcula variações absolutas e percentuais anuais da participação."""
    return calcular_participacao_anual(df, coluna_valor)


def calcular_crescimento_municipal(
    df: pd.DataFrame,
    ano_inicial: int | None = None,
    ano_final: int | None = None,
    coluna_valor: str = "n_participantes",
) -> pd.DataFrame:
    """
    Compara municípios entre dois anos explicitamente selecionados.
    Só calcula crescimento percentual quando a base inicial é positiva.
    """
    validar_colunas(
        df,
        ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO", coluna_valor],
        "painel",
    )
    dados = df.copy()
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados[coluna_valor] = pd.to_numeric(dados[coluna_valor], errors="coerce")

    anos = sorted(dados["ano"].dropna().astype(int).unique())
    if not anos:
        return pd.DataFrame()
    ano_inicial = anos[0] if ano_inicial is None else ano_inicial
    ano_final = anos[-1] if ano_final is None else ano_final

    recorte = dados.loc[dados["ano"].isin([ano_inicial, ano_final])]
    tabela = recorte.pivot_table(
        index=["CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO"],
        columns="ano",
        values=coluna_valor,
        aggfunc="sum",
    ).reset_index()
    tabela = tabela.rename(
        columns={ano_inicial: "participantes_inicial", ano_final: "participantes_final"}
    )
    for col in ["participantes_inicial", "participantes_final"]:
        if col not in tabela:
            tabela[col] = np.nan
    tabela["variacao_absoluta"] = (
        tabela["participantes_final"] - tabela["participantes_inicial"]
    )
    tabela["variacao_percentual"] = np.where(
        tabela["participantes_inicial"] > 0,
        tabela["variacao_absoluta"] / tabela["participantes_inicial"] * 100,
        np.nan,
    )
    tabela["ano_inicial"] = ano_inicial
    tabela["ano_final"] = ano_final
    tabela["comparavel"] = tabela[
        ["participantes_inicial", "participantes_final"]
    ].notna().all(axis=1)
    return tabela.sort_values("variacao_absoluta", ascending=False).reset_index(drop=True)


def calcular_participacao_municipal(
    df: pd.DataFrame,
    coluna_valor: str = "n_participantes",
) -> pd.DataFrame:
    """Calcula a participação percentual de cada município no total de cada ano."""
    validar_colunas(
        df, ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO", coluna_valor],
        "painel",
    )
    dados = df.copy()
    dados[coluna_valor] = pd.to_numeric(dados[coluna_valor], errors="coerce")
    dados["total_estadual"] = dados.groupby("ano")[coluna_valor].transform("sum")
    dados["participacao_pct"] = np.where(
        dados["total_estadual"] > 0,
        dados[coluna_valor] / dados["total_estadual"] * 100,
        np.nan,
    )
    return dados


def _gini(valores: np.ndarray) -> float:
    """Calcula o coeficiente de Gini para valores não negativos."""
    x = np.asarray(valores, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0 or np.any(x < 0) or x.sum() == 0:
        return np.nan
    x = np.sort(x)
    n = len(x)
    return float((2 * np.sum(np.arange(1, n + 1) * x) / (n * x.sum())) - (n + 1) / n)


def calcular_concentracao_municipal(
    df: pd.DataFrame,
    coluna_valor: str = "n_participantes",
) -> pd.DataFrame:
    """Calcula HHI, Gini e concentração dos cinco e dez maiores municípios por ano."""
    validar_colunas(df, ["ano", "CO_MUNICIPIO_TERRITORIO", coluna_valor], "painel")
    dados = df.copy()
    dados[coluna_valor] = pd.to_numeric(dados[coluna_valor], errors="coerce")
    resultados = []
    for ano, grupo in dados.groupby("ano"):
        valores = grupo[coluna_valor].dropna()
        valores = valores.clip(lower=0)
        total = valores.sum()
        shares = valores / total if total > 0 else pd.Series(dtype=float)
        ordenados = valores.sort_values(ascending=False)
        resultados.append({
            "ano": ano,
            "n_municipios": int(valores.size),
            "participantes_total": float(total),
            "hhi": float((shares ** 2).sum()) if len(shares) else np.nan,
            "hhi_escala_10000": float((shares ** 2).sum() * 10000) if len(shares) else np.nan,
            "gini": _gini(valores.to_numpy()),
            "top5_pct": float(ordenados.head(5).sum() / total * 100) if total > 0 else np.nan,
            "top10_pct": float(ordenados.head(10).sum() / total * 100) if total > 0 else np.nan,
        })
    return pd.DataFrame(resultados).sort_values("ano").reset_index(drop=True)



def calcular_indicadores_temporais(
    df_anual: pd.DataFrame,
    coluna_valor: str = "participantes",
    janela: int = 3,
) -> pd.DataFrame:
    """
    Calcula indicadores temporais da participação anual.

    Indicadores:
    - Variação absoluta anual;
    - Variação percentual anual;
    - Crescimento acumulado em relação ao primeiro ano;
    - CAGR do período completo;
    - Média móvel centrada.

    O CAGR é repetido nas linhas para facilitar sua consulta na tabela,
    mas representa o período completo, não uma taxa anual individual.
    """
    validar_colunas(df_anual, ["ano", coluna_valor], "df_anual")

    if not isinstance(janela, int) or janela < 1:
        raise ValueError("'janela' deve ser um inteiro positivo.")

    dados = df_anual.copy()
    if "cagr_pct" in dados.columns:
        dados = dados.drop(columns=["cagr_pct"])


    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados[coluna_valor] = pd.to_numeric(
        dados[coluna_valor], errors="coerce"
    )

    dados = (
        dados.dropna(subset=["ano"])
        .sort_values("ano")
        .reset_index(drop=True)
    )

    if dados.empty:
        return dados

    # Evita cálculos inconsistentes com anos duplicados.
    if dados["ano"].duplicated().any():
        raise ValueError("Existem anos duplicados na série anual.")

    # Variação absoluta e percentual anual
    dados["variacao_absoluta"] = dados[coluna_valor].diff()

    dados["variacao_percentual"] = (
        dados[coluna_valor].pct_change(fill_method=None) * 100
    )

    # Crescimento acumulado em relação ao primeiro ano válido
    validos = dados.dropna(subset=[coluna_valor])

    if not validos.empty:
        valor_inicial = validos.iloc[0][coluna_valor]

        if valor_inicial > 0:
            dados["crescimento_acumulado_pct"] = (
                dados[coluna_valor] / valor_inicial - 1
            ) * 100
        else:
            dados["crescimento_acumulado_pct"] = np.nan

        # CAGR do período completo
        ano_inicial = validos.iloc[0]["ano"]
        ano_final = validos.iloc[-1]["ano"]
        valor_final = validos.iloc[-1][coluna_valor]
        intervalo = ano_final - ano_inicial

        if valor_inicial > 0 and valor_final > 0 and intervalo > 0:
            cagr = (
                (valor_final / valor_inicial) ** (1 / intervalo) - 1
            ) * 100
        else:
            cagr = np.nan

        dados["cagr_periodo_pct"] = cagr

    else:
        dados["crescimento_acumulado_pct"] = np.nan
        dados["cagr_periodo_pct"] = np.nan

    # Média móvel centrada
    dados["media_movel"] = dados[coluna_valor].rolling(
        window=janela,
        center=True,
        min_periods=1,
    ).mean()

    return dados



def calcular_taxa_presenca(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalcula presença e ausência a partir das contagens informadas.
    Não preenche anos sem denominador válido.
    """
    validar_colunas(
        df,
        ["ano", "n_presentes", "n_ausentes", "n_presenca_informada"],
        "painel",
    )
    dados = df.copy()
    for col in ["n_presentes", "n_ausentes", "n_presenca_informada"]:
        dados[col] = pd.to_numeric(dados[col], errors="coerce")
    dados["pct_presenca_calculada"] = np.where(
        dados["n_presenca_informada"] > 0,
        dados["n_presentes"] / dados["n_presenca_informada"] * 100,
        np.nan,
    )
    dados["pct_ausencia_calculada"] = np.where(
        dados["n_presenca_informada"] > 0,
        dados["n_ausentes"] / dados["n_presenca_informada"] * 100,
        np.nan,
    )
    dados["soma_presenca_ausencia"] = dados["n_presentes"] + dados["n_ausentes"]
    dados["diferenca_denominador"] = (
        dados["n_presenca_informada"] - dados["soma_presenca_ausencia"]
    )
    return dados


def plotar_serie_temporal(
    df: pd.DataFrame,
    x: str,
    y: str,
    titulo: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    ax=None,
    **kwargs,
):
    """Cria uma série temporal com Seaborn e retorna o eixo."""
    validar_colunas(df, [x, y])
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=df, x=x, y=y, marker="o", ax=ax, **kwargs)
    ax.set(title=titulo, xlabel=xlabel or x, ylabel=ylabel or y)
    ax.grid(True, alpha=0.25)
    return ax


def plotar_comparacao_municipal(
    df: pd.DataFrame,
    x: str,
    y: str,
    titulo: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    top_n: int | None = 15,
    ax=None,
    **kwargs,
):
    """Cria gráfico de barras horizontal para comparação municipal."""
    validar_colunas(df, [x, y])
    dados = df.nlargest(top_n, y) if top_n is not None else df.copy()
    dados = dados.sort_values(y, ascending=True)
    if ax is None:
        altura = max(5, 0.35 * len(dados))
        _, ax = plt.subplots(figsize=(11, altura))
    sns.barplot(data=dados, x=y, y=x, ax=ax, **kwargs)
    ax.set(title=titulo, xlabel=xlabel or y, ylabel=y)
    ax.grid(axis="x", alpha=0.25)
    return ax


def padronizar_presenca_ausencia(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Padroniza os indicadores de presença e ausência do ENEM.

    1998-2008: dados diretos de presença e ausência.
    2009-2016: n_validos_cn como referência.
    2017-2025: n_validos_redacao como referência.
    """

    colunas = [
        "ano",
        "n_participantes",
        "n_presentes",
        "n_ausentes",
        "n_validos_cn",
        "n_validos_redacao",
    ]

    validar_colunas(df, colunas, "df")

    dados = df.copy()

    # Preservar os valores originais de presença e ausência
    presentes_originais = pd.to_numeric(
        dados["n_presentes"], errors="coerce"
    )

    ausentes_originais = pd.to_numeric(
        dados["n_ausentes"], errors="coerce"
    )

    # Garantir tipos numéricos
    for coluna in [
        "ano",
        "n_participantes",
        "n_validos_cn",
        "n_validos_redacao",
    ]:
        dados[coluna] = pd.to_numeric(
            dados[coluna], errors="coerce"
        )

    # Inicializar indicadores padronizados
    dados["n_presentes"] = np.nan
    dados["n_ausentes"] = np.nan
    dados["metodo_presenca"] = pd.NA

    # 1998-2008: prova única
    mask_1 = dados["ano"].between(1998, 2008)

    dados.loc[mask_1, "n_presentes"] = presentes_originais.loc[mask_1]
    dados.loc[mask_1, "n_ausentes"] = ausentes_originais.loc[mask_1]
    dados.loc[mask_1, "metodo_presenca"] = "DIRETO"

    # 2009-2016: CN como referência
    mask_2 = dados["ano"].between(2009, 2016)

    dados.loc[mask_2, "n_presentes"] = dados.loc[
        mask_2, "n_validos_cn"
    ]

    dados.loc[mask_2, "n_ausentes"] = (
        dados.loc[mask_2, "n_participantes"]
        - dados.loc[mask_2, "n_validos_cn"]
    )

    dados.loc[mask_2, "metodo_presenca"] = "VALIDOS_CN"

    # 2017-2025: redação como referência
    mask_3 = dados["ano"].between(2017, 2025)

    dados.loc[mask_3, "n_presentes"] = dados.loc[
        mask_3, "n_validos_redacao"
    ]

    dados.loc[mask_3, "n_ausentes"] = (
        dados.loc[mask_3, "n_participantes"]
        - dados.loc[mask_3, "n_validos_redacao"]
    )

    dados.loc[mask_3, "metodo_presenca"] = "VALIDOS_REDACAO"

    # Total com informação disponível
    dados["n_presenca_informada"] = (
        dados["n_presentes"] + dados["n_ausentes"]
    )

    return dados



# ---------------------------------------------------------------------
# EIXO 2 — DESIGUALDADE DE GÊNERO
# ---------------------------------------------------------------------

def _resolver_coluna_media(
    df: pd.DataFrame,
    coluna_media: str | None = None,
) -> str:
    """Localiza a coluna de média disponível no resumo DSP."""
    if coluna_media is not None:
        validar_colunas(df, [coluna_media], "dsp")
        return coluna_media

    candidatas = [
        "media_ponderada", "media", "nota_media",
        "media_nota", "nu_media", "media_resultado",
    ]
    encontrada = next((c for c in candidatas if c in df.columns), None)
    if encontrada is None:
        raise ValueError(
            "Não foi identificada a coluna de média no DSP. "
            f"Colunas disponíveis: {df.columns.tolist()}. "
            "Informe explicitamente coluna_media."
        )
    return encontrada


def _normalizar_sexo(serie: pd.Series) -> pd.Series:
    """Padroniza rótulos de sexo sem classificar valores desconhecidos."""
    valores = serie.astype("string").str.strip().str.upper()
    mapa = {
        "M": "MASCULINO", "MASC": "MASCULINO",
        "MASCULINO": "MASCULINO", "1": "MASCULINO",
        "F": "FEMININO", "FEM": "FEMININO",
        "FEMININO": "FEMININO", "2": "FEMININO",
    }
    return valores.map(mapa).fillna(valores)


def auditar_genero(
    painel: pd.DataFrame,
    dsp: pd.DataFrame,
    referencia: str = "ESC",
) -> dict:
    """
    Audita as bases necessárias ao Eixo 2.

    O painel deve conter contagens municipais por sexo. O DSP deve conter
    ano, sexo, disciplina, número de notas válidas e uma coluna de média.
    A função não altera os DataFrames recebidos.
    """
    obrigatorias_painel = [
        "ano", "CO_MUNICIPIO_TERRITORIO",
        "NO_MUNICIPIO_TERRITORIO", "n_participantes",
        "n_masculino", "n_feminino",
    ]
    validar_colunas(painel, obrigatorias_painel, "painel")

    dados_painel = filtrar_referencia(painel, referencia)
    dados_painel = dados_painel.copy()
    dados_painel["ano"] = pd.to_numeric(dados_painel["ano"], errors="coerce")
    for coluna in ["n_participantes", "n_masculino", "n_feminino"]:
        dados_painel[coluna] = pd.to_numeric(
            dados_painel[coluna], errors="coerce"
        )

    obrigatorias_dsp = ["ano", "sexo", "disciplina", "n_validos"]
    validar_colunas(dsp, obrigatorias_dsp, "dsp")
    coluna_media = _resolver_coluna_media(dsp)

    dados_dsp = filtrar_referencia(dsp, referencia).copy()
    dados_dsp["ano"] = pd.to_numeric(dados_dsp["ano"], errors="coerce")
    dados_dsp["sexo"] = _normalizar_sexo(dados_dsp["sexo"])

    chaves_painel = [
        c for c in ["ano", "CO_MUNICIPIO_TERRITORIO"]
        if c in dados_painel.columns
    ]
    dimensoes_dsp = [
        c for c in [
            "ano", "CO_MUNICIPIO_TERRITORIO", "sexo",
            "disciplina", "faixa_etaria", "grupo_etario",
            "dependencia_administrativa",
        ] if c in dados_dsp.columns
    ]

    duplicidades_painel = dados_painel.loc[
        dados_painel.duplicated(chaves_painel, keep=False)
    ].sort_values(chaves_painel) if chaves_painel else pd.DataFrame()

    duplicidades_dsp = dados_dsp.loc[
        dados_dsp.duplicated(dimensoes_dsp, keep=False)
    ].sort_values(dimensoes_dsp) if dimensoes_dsp else pd.DataFrame()

    anual_painel = (
        dados_painel.groupby("ano", as_index=False)
        .agg(
            n_municipios=("CO_MUNICIPIO_TERRITORIO", "nunique"),
            participantes=("n_participantes", "sum"),
            masculino=("n_masculino", lambda s: s.sum(min_count=1)),
            feminino=("n_feminino", lambda s: s.sum(min_count=1)),
        )
        .sort_values("ano")
    )
    anual_dsp = (
        dados_dsp.groupby(["ano", "disciplina"], as_index=False)
        .agg(
            n_validos=("n_validos", "sum"),
            n_registros=("n_validos", "size"),
        )
        .sort_values(["ano", "disciplina"])
    )
    cobertura_dsp = (
        dados_dsp.groupby(["ano", "disciplina", "sexo"], as_index=False)
        .agg(
            n_municipios=(
                "CO_MUNICIPIO_TERRITORIO", "nunique"
            ) if "CO_MUNICIPIO_TERRITORIO" in dados_dsp.columns
            else ("n_validos", "size"),
            n_validos=("n_validos", "sum"),
            n_registros=("n_validos", "size"),
        )
        .sort_values(["ano", "disciplina", "sexo"])
    )

    return {
        "referencia": referencia,
        "coluna_media_dsp": coluna_media,
        "anos_painel": sorted(dados_painel["ano"].dropna().astype(int).unique()),
        "anos_dsp": sorted(dados_dsp["ano"].dropna().astype(int).unique()),
        "sexos_dsp": sorted(dados_dsp["sexo"].dropna().astype(str).unique()),
        "disciplinas_dsp": sorted(dados_dsp["disciplina"].dropna().astype(str).unique()),
        "duplicidades_painel": duplicidades_painel,
        "duplicidades_dsp": duplicidades_dsp,
        "anual_painel": anual_painel,
        "cobertura_dsp": cobertura_dsp,
        "painel": dados_painel,
        "dsp": dados_dsp,
    }


def calcular_participacao_genero(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Agrega a participação anual por sexo.

    Os percentuais masculino/feminino usam como denominador a soma dos
    dois grupos informados. A diferença para n_participantes permanece
    identificada como sexo não informado.
    """
    validar_colunas(
        df,
        ["ano", "n_participantes", "n_masculino", "n_feminino"],
        "painel",
    )
    dados = df.copy()
    for col in ["ano", "n_participantes", "n_masculino", "n_feminino"]:
        dados[col] = pd.to_numeric(dados[col], errors="coerce")

    agregacoes = {
        "participantes": ("n_participantes", "sum"),
        "masculino": ("n_masculino", lambda s: s.sum(min_count=1)),
        "feminino": ("n_feminino", lambda s: s.sum(min_count=1)),
    }
    if "CO_MUNICIPIO_TERRITORIO" in dados.columns:
        agregacoes["n_municipios"] = ("CO_MUNICIPIO_TERRITORIO", "nunique")

    resultado = (
        dados.groupby("ano", as_index=False)
        .agg(**agregacoes)
        .sort_values("ano")
        .reset_index(drop=True)
    )
    resultado["sexo_informado"] = resultado["masculino"] + resultado["feminino"]
    resultado["sexo_nao_informado"] = (
        resultado["participantes"] - resultado["sexo_informado"]
    )
    # Pequenas divergências negativas são mantidas para auditoria, não ocultadas.
    denominador = resultado["sexo_informado"].where(
        resultado["sexo_informado"] > 0
    )
    resultado["pct_masculino"] = resultado["masculino"] / denominador * 100
    resultado["pct_feminino"] = resultado["feminino"] / denominador * 100
    resultado["pct_sexo_nao_informado"] = np.where(
        resultado["participantes"] > 0,
        resultado["sexo_nao_informado"] / resultado["participantes"] * 100,
        np.nan,
    )
    resultado["diferenca_feminino_masculino_pp"] = (
        resultado["pct_feminino"] - resultado["pct_masculino"]
    )
    return resultado


def calcular_participacao_genero_municipal(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula contagens e composição por sexo para cada município e ano."""
    validar_colunas(
        df,
        [
            "ano", "CO_MUNICIPIO_TERRITORIO",
            "NO_MUNICIPIO_TERRITORIO", "n_participantes",
            "n_masculino", "n_feminino",
        ],
        "painel",
    )
    dados = df.copy()
    for col in ["ano", "n_participantes", "n_masculino", "n_feminino"]:
        dados[col] = pd.to_numeric(dados[col], errors="coerce")

    resultado = (
        dados.groupby(
            ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO"],
            as_index=False,
            dropna=False,
        )
        .agg(
            n_participantes=("n_participantes", "sum"),
            n_masculino=("n_masculino", lambda s: s.sum(min_count=1)),
            n_feminino=("n_feminino", lambda s: s.sum(min_count=1)),
        )
    )
    resultado["sexo_informado"] = (
        resultado["n_masculino"] + resultado["n_feminino"]
    )
    resultado["sexo_nao_informado"] = (
        resultado["n_participantes"] - resultado["sexo_informado"]
    )
    denominador = resultado["sexo_informado"].where(
        resultado["sexo_informado"] > 0
    )
    resultado["pct_masculino"] = resultado["n_masculino"] / denominador * 100
    resultado["pct_feminino"] = resultado["n_feminino"] / denominador * 100
    resultado["pct_sexo_nao_informado"] = np.where(
        resultado["n_participantes"] > 0,
        resultado["sexo_nao_informado"] / resultado["n_participantes"] * 100,
        np.nan,
    )
    resultado["diferenca_feminino_masculino_pp"] = (
        resultado["pct_feminino"] - resultado["pct_masculino"]
    )
    return resultado.sort_values(
        ["ano", "NO_MUNICIPIO_TERRITORIO"]
    ).reset_index(drop=True)


def calcular_desempenho_genero(
    df: pd.DataFrame,
    por_municipio: bool = False,
    coluna_media: str | None = None,
) -> pd.DataFrame:
    """
    Calcula médias estaduais ou municipais por sexo e disciplina.

    As médias são ponderadas por n_validos. Se o DSP possuir estratos
    adicionais (por exemplo, faixa etária), eles são agregados sem fazer
    média simples das médias dos estratos.
    """
    validar_colunas(
        df, ["ano", "sexo", "disciplina", "n_validos"], "dsp"
    )
    col_media = _resolver_coluna_media(df, coluna_media)

    dimensoes = ["ano", "disciplina", "sexo"]
    if por_municipio:
        validar_colunas(
            df,
            ["CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO"],
            "dsp",
        )
        dimensoes = [
            "ano", "CO_MUNICIPIO_TERRITORIO",
            "NO_MUNICIPIO_TERRITORIO", "disciplina", "sexo",
        ]

    dados = df.copy()
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados["n_validos"] = pd.to_numeric(dados["n_validos"], errors="coerce")
    dados[col_media] = pd.to_numeric(dados[col_media], errors="coerce")
    dados["sexo"] = _normalizar_sexo(dados["sexo"])
    dados = dados.loc[
        dados["sexo"].isin(["MASCULINO", "FEMININO"])
        & dados["n_validos"].gt(0)
        & dados[col_media].notna()
    ].copy()

    dados["_soma_ponderada"] = dados[col_media] * dados["n_validos"]
    resultado = (
        dados.groupby(dimensoes, as_index=False, dropna=False)
        .agg(
            soma_ponderada=("_soma_ponderada", "sum"),
            n_validos=("n_validos", "sum"),
            n_registros=("n_validos", "size"),
        )
    )
    resultado["media_ponderada"] = (
        resultado["soma_ponderada"] / resultado["n_validos"]
    )
    return resultado.drop(columns="soma_ponderada").sort_values(
        dimensoes
    ).reset_index(drop=True)


def calcular_gap_desempenho_genero(
    df: pd.DataFrame,
    por_municipio: bool = False,
) -> pd.DataFrame:
    """
    Calcula o gap feminino − masculino em pontos da escala da disciplina.
    Recebe a saída de calcular_desempenho_genero.
    """
    chaves = ["ano", "disciplina"]
    if por_municipio:
        chaves = [
            "ano", "CO_MUNICIPIO_TERRITORIO",
            "NO_MUNICIPIO_TERRITORIO", "disciplina",
        ]
    validar_colunas(
        df,
        chaves + ["sexo", "media_ponderada", "n_validos"],
        "desempenho_genero",
    )
    dados = df.copy()
    dados["sexo"] = _normalizar_sexo(dados["sexo"])

    medias = dados.pivot_table(
        index=chaves,
        columns="sexo",
        values="media_ponderada",
        aggfunc="first",
    ).reset_index()
    contagens = dados.pivot_table(
        index=chaves,
        columns="sexo",
        values="n_validos",
        aggfunc="sum",
    ).reset_index()

    medias.columns.name = None
    contagens.columns.name = None
    renomear_medias = {}
    renomear_contagens = {}
    if "FEMININO" in medias.columns:
        renomear_medias["FEMININO"] = "media_feminina"
    if "MASCULINO" in medias.columns:
        renomear_medias["MASCULINO"] = "media_masculina"
    if "FEMININO" in contagens.columns:
        renomear_contagens["FEMININO"] = "n_validos_feminino"
    if "MASCULINO" in contagens.columns:
        renomear_contagens["MASCULINO"] = "n_validos_masculino"

    medias = medias.rename(columns=renomear_medias)
    contagens = contagens.rename(columns=renomear_contagens)
    resultado = medias.merge(contagens, on=chaves, how="outer")

    for col in [
        "media_feminina", "media_masculina",
        "n_validos_feminino", "n_validos_masculino",
    ]:
        if col not in resultado.columns:
            resultado[col] = np.nan

    resultado["gap_feminino_masculino"] = (
        resultado["media_feminina"] - resultado["media_masculina"]
    )
    return resultado.sort_values(chaves).reset_index(drop=True)

# ---------------------------------------------------------------------
# EIXO 3 — DEPENDÊNCIA ADMINISTRATIVA DA ESCOLA
# ---------------------------------------------------------------------

MAPA_DEPENDENCIA_ESCOLAR = {
    "1": "FEDERAL", "FEDERAL": "FEDERAL",
    "2": "ESTADUAL", "ESTADUAL": "ESTADUAL",
    "3": "MUNICIPAL", "MUNICIPAL": "MUNICIPAL",
    "4": "PRIVADA", "PRIVADA": "PRIVADA",
    "NAO_INFORMADA": "NAO_INFORMADA",
    "NÃO INFORMADA": "NAO_INFORMADA",
    "NÃO_INFORMADO": "NAO_INFORMADA",
    "NAN": "NAO_INFORMADA",
    "<NA>": "NAO_INFORMADA",
}


def normalizar_dependencia_escolar(serie: pd.Series) -> pd.Series:
    """Padroniza categorias de dependência administrativa escolar."""
    valores = serie.astype("string").str.strip().str.upper()
    valores = valores.str.replace(r"\s+", " ", regex=True)
    return valores.map(MAPA_DEPENDENCIA_ESCOLAR).fillna(valores)


def calcular_participacao_dependencia(
    painel: pd.DataFrame,
    incluir_nao_informada: bool = True,
    anos_sem_informacao: tuple[int, ...] = (1998, 1999, 2000),
) -> pd.DataFrame:
    """
    Agrega participantes por ano e dependência administrativa.

    A dependência administrativa não está disponível em 1998–2000.
    Nesses anos, as contagens e percentuais por categoria são mantidos
    como ausentes (NaN), nunca convertidos em zero.

    Os percentuais das quatro categorias classificadas usam como
    denominador o total de dependências classificadas. A categoria
    não informada é preservada separadamente.
    """
    colunas = [
        "ano", "n_escola_federal", "n_escola_estadual",
        "n_escola_municipal", "n_escola_privada",
    ]
    validar_colunas(painel, colunas, "painel")
    dados = painel.copy()
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    contagens = {
        "FEDERAL": "n_escola_federal",
        "ESTADUAL": "n_escola_estadual",
        "MUNICIPAL": "n_escola_municipal",
        "PRIVADA": "n_escola_privada",
    }
    if "n_escola_nao_informada" in dados.columns:
        contagens["NAO_INFORMADA"] = "n_escola_nao_informada"

    for coluna in contagens.values():
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")

    anual = dados.groupby("ano", as_index=False).agg(
        **{
            nome.lower(): (coluna, lambda s: s.sum(min_count=1))
            for nome, coluna in contagens.items()
        }
    ).sort_values("ano")

    anos_sem_info = anual["ano"].isin(anos_sem_informacao)
    colunas_categoria = [
        nome.lower() for nome in contagens
    ]
    anual.loc[anos_sem_info, colunas_categoria] = np.nan

    classificadas = [
        nome.lower() for nome in ["FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA"]
        if nome.lower() in anual.columns
    ]
    anual["n_dependencia_classificada"] = anual[classificadas].sum(
        axis=1, min_count=1
    )
    if "nao_informada" not in anual.columns:
        anual["nao_informada"] = np.nan
    anual["n_dependencia_nao_informada"] = anual["nao_informada"]

    denominador = anual["n_dependencia_classificada"].where(
        anual["n_dependencia_classificada"].gt(0)
    )
    for nome in ["federal", "estadual", "municipal", "privada"]:
        anual[f"pct_{nome}"] = anual[nome].div(denominador) * 100

    anual["pct_nao_informada_sobre_participantes"] = np.nan
    if "n_participantes" in dados.columns:
        total_participantes = dados.groupby("ano")["n_participantes"].sum(min_count=1)
        anual = anual.merge(
            total_participantes.rename("n_participantes"),
            on="ano", how="left",
        )
        denominador_total = anual["n_participantes"].where(
            anual["n_participantes"].gt(0)
        )
        anual["pct_nao_informada_sobre_participantes"] = (
            anual["n_dependencia_nao_informada"].div(denominador_total) * 100
        )

    if not incluir_nao_informada:
        anual = anual.drop(columns=["nao_informada", "n_dependencia_nao_informada"])
    return anual.reset_index(drop=True)

def preparar_desempenho_dependencia(
    grupo: pd.DataFrame,
    referencia: str = "ESC",
) -> pd.DataFrame:
    """
    Seleciona estatísticas por dependência escolar (tipo_grupo=ESCOLA).

    A base de consumo tem granularidade município-ano-categoria-disciplina.
    Portanto, mediana, quartis e desvio-padrão são estatísticas municipais;
    não podem ser recombinados para reconstruir a distribuição estadual
    dos participantes. As notas de 1998–2008 (Objetiva e Redação) são
    multiplicadas por 10 para padronização na escala 0–1000.
    """
    obrigatorias = [
        "ano", "tipo_grupo", "grupo", "disciplina", "n_validos",
        "media", "mediana", "std", "q1", "q3",
        "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO",
    ]
    validar_colunas(grupo, obrigatorias, "grupo")
    dados = filtrar_referencia(grupo, referencia)
    dados = dados.loc[
        dados["tipo_grupo"].astype("string").str.upper().eq("ESCOLA")
    ].copy()
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados["n_validos"] = pd.to_numeric(dados["n_validos"], errors="coerce")
    for coluna in ["media", "mediana", "std", "q1", "q3"]:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
    dados["dependencia"] = normalizar_dependencia_escolar(dados["grupo"])
    categorias = ["FEDERAL", "ESTADUAL", "MUNICIPAL", "PRIVADA", "NAO_INFORMADA"]
    dados = dados.loc[
        dados["dependencia"].isin(categorias)
        & dados["n_validos"].gt(0)
    ].copy()

    # Padronização da escala de notas para 0–1000.
    # Até 2008: Objetiva e Redação em 0–100; multiplicar por 10.
    # De 2009 em diante: escalas já expressas em 0–1000.
    disciplinas_pre_2009 = dados["disciplina"].astype("string").str.upper().isin(
        ["OBJETIVA", "REDACAO"]
    )
    mascara_escala_100 = dados["ano"].le(2008) & disciplinas_pre_2009
    colunas_notas = ["media", "mediana", "std", "q1", "q3"]
    dados.loc[mascara_escala_100, colunas_notas] = (
        dados.loc[mascara_escala_100, colunas_notas] * 10
    )
    dados["escala_padronizada"] = "0-1000"
    return dados.sort_values(
        ["ano", "disciplina", "dependencia", "NO_MUNICIPIO_TERRITORIO"]
    ).reset_index(drop=True)


def agregar_desempenho_dependencia(
    dados: pd.DataFrame,
    por_municipio: bool = False,
) -> pd.DataFrame:
    """
    Agrega médias ponderadas por n_validos e resume estatísticas municipais.

    `media_ponderada` é uma média de médias municipais ponderada por notas
    válidas. `mediana_municipal_mediana`, `q1_municipal_mediana`,
    `q3_municipal_mediana` e `std_municipal_mediana` resumem distribuições
    de estatísticas municipais; não são estatísticas individuais estaduais.
    """
    chaves = ["ano", "disciplina", "dependencia"]
    if por_municipio:
        chaves = [
            "ano", "CO_MUNICIPIO_TERRITORIO",
            "NO_MUNICIPIO_TERRITORIO", "disciplina", "dependencia",
        ]
    validar_colunas(
        dados, chaves + ["n_validos", "media", "mediana", "std", "q1", "q3"],
        "dados_dependencia",
    )
    base = dados.copy()
    base["_soma_ponderada"] = base["media"] * base["n_validos"]
    resultado = base.groupby(chaves, as_index=False, dropna=False).agg(
        soma_ponderada=("_soma_ponderada", "sum"),
        n_validos=("n_validos", "sum"),
        n_municipios=("CO_MUNICIPIO_TERRITORIO", "nunique"),
        mediana_municipal_mediana=("mediana", "median"),
        q1_municipal_mediana=("mediana", lambda s: s.quantile(0.25)),
        q3_municipal_mediana=("mediana", lambda s: s.quantile(0.75)),
        mediana_q1_municipal=("q1", "median"),
        mediana_q3_municipal=("q3", "median"),
        std_municipal_mediana=("std", "median"),
        mediana_q1=("q1", "median"),
        mediana_q3=("q3", "median"),
    )
    resultado["media_ponderada"] = resultado["soma_ponderada"] / resultado["n_validos"]
    return resultado.drop(columns="soma_ponderada").sort_values(chaves).reset_index(drop=True)


def calcular_gap_publica_privada(
    desempenho: pd.DataFrame,
    por_municipio: bool = False,
) -> pd.DataFrame:
    """Calcula média pública agrupada menos média privada."""
    chaves = ["ano", "disciplina"]
    if por_municipio:
        chaves = [
            "ano", "CO_MUNICIPIO_TERRITORIO",
            "NO_MUNICIPIO_TERRITORIO", "disciplina",
        ]
    validar_colunas(
        desempenho, chaves + ["dependencia", "media_ponderada", "n_validos"],
        "desempenho",
    )
    dados = desempenho.copy()
    dados["setor"] = np.where(
        dados["dependencia"].isin(["FEDERAL", "ESTADUAL", "MUNICIPAL"]),
        "PUBLICA",
        np.where(dados["dependencia"].eq("PRIVADA"), "PRIVADA", "NAO_INFORMADA"),
    )
    dados = dados.loc[dados["setor"].isin(["PUBLICA", "PRIVADA"])]
    dados["_soma"] = dados["media_ponderada"] * dados["n_validos"]
    agregado = dados.groupby(chaves + ["setor"], as_index=False).agg(
        soma_ponderada=("_soma", "sum"),
        n_validos=("n_validos", "sum"),
    )
    agregado["media_ponderada_setor"] = agregado["soma_ponderada"] / agregado["n_validos"]
    medias = agregado.pivot(index=chaves, columns="setor", values="media_ponderada_setor").reset_index()
    contagens = agregado.pivot(index=chaves, columns="setor", values="n_validos").reset_index()
    medias.columns.name = None
    contagens.columns.name = None
    contagens = contagens.rename(columns={
        "PUBLICA": "n_validos_publica", "PRIVADA": "n_validos_privada"
    })
    resultado = medias.merge(contagens, on=chaves, how="left")
    if "PUBLICA" not in resultado:
        resultado["PUBLICA"] = np.nan
    if "PRIVADA" not in resultado:
        resultado["PRIVADA"] = np.nan
    resultado["gap_publica_menos_privada"] = resultado["PUBLICA"] - resultado["PRIVADA"]
    return resultado.sort_values(chaves).reset_index(drop=True)


def exportar_resultados_excel(
    resultados: dict[str, pd.DataFrame],
    caminho: str | Path,
) -> Path:
    """Exporta um dicionário de DataFrames para abas de um único Excel."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        for nome, tabela in resultados.items():
            if not isinstance(tabela, pd.DataFrame):
                continue
            aba = str(nome)[:31]
            tabela.to_excel(writer, sheet_name=aba, index=False)
    return caminho


# ---------------------------------------------------------------------
# EIXO 4 — IDADE E TRAJETÓRIA DOS PARTICIPANTES
# ---------------------------------------------------------------------

MAPA_FAIXA_5 = {
    1: "<17",
    2: "17–20", 3: "17–20", 4: "17–20", 5: "17–20",
    6: "21–25", 7: "21–25", 8: "21–25", 9: "21–25", 10: "21–25",
    11: "26–40", 12: "26–40", 13: "26–40",
    14: ">40", 15: ">40", 16: ">40", 17: ">40", 18: ">40",
    19: ">40", 20: ">40",
}
ORDEM_FAIXAS = ["<17", "17–20", "21–25", "26–40", ">40"]
MAPA_FAIXA_ETARIA = {str(k): v for k, v in MAPA_FAIXA_5.items()}


def _normalizar_faixa_etaria_eixo6(serie: pd.Series) -> pd.Series:
    """Aplica MAPA_FAIXA_5 e preserva rótulos já normalizados/especiais."""
    valores = serie.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    mapa = {str(k): v for k, v in MAPA_FAIXA_5.items()}
    mapa.update({rotulo: rotulo for rotulo in ORDEM_FAIXAS})
    normalizados = valores.map(mapa)
    # Categorias não numéricas como NAO_INFORMADO são preservadas.
    # Códigos numéricos fora de 1–20 são sinalizados para evitar classificação incorreta.
    numericos = valores.str.fullmatch(r"\d+").fillna(False)
    desconhecidos = numericos & normalizados.isna()
    if desconhecidos.any():
        codigos = sorted(valores.loc[desconhecidos].unique().tolist())
        raise ValueError(f"Códigos de faixa etária sem mapeamento em MAPA_FAIXA_5: {codigos}")
    return normalizados.fillna(valores)


def normalizar_faixa_etaria(serie: pd.Series, mapa: dict | None = None) -> pd.Series:
    """Converte códigos de TP_FAIXA_ETARIA nas cinco categorias analíticas."""
    mapa = MAPA_FAIXA_5 if mapa is None else mapa
    valores = serie.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    mapa_normalizado = {str(k): v for k, v in mapa.items()}
    rotulos = valores.map(mapa_normalizado)
    desconhecidos = valores.notna() & rotulos.isna()
    if desconhecidos.any():
        codigos = sorted(valores.loc[desconhecidos].unique().tolist())
        raise ValueError(f"Códigos de faixa etária sem mapeamento: {codigos}")
    return pd.Categorical(rotulos, categories=ORDEM_FAIXAS, ordered=True)


def _resolver_coluna(df: pd.DataFrame, candidatas: list[str], nome: str) -> str:
    encontrada = next((c for c in candidatas if c in df.columns), None)
    if encontrada is None:
        raise ValueError(
            f"Não foi identificada a coluna {nome}. "
            f"Candidatas: {candidatas}. Colunas disponíveis: {df.columns.tolist()}"
        )
    return encontrada


def preparar_participacao_idade(
    faixa: pd.DataFrame,
    coluna_contagem: str | None = None,
    coluna_faixa: str | None = None,
    coluna_sexo: str | None = None,
) -> pd.DataFrame:
    """Padroniza a base faixa para I01–I02, preservando sua granularidade."""
    validar_colunas(faixa, ["ano"], "faixa")
    dados = faixa.copy()
    coluna_faixa = coluna_faixa or _resolver_coluna(
        dados, ["faixa_etaria", "TP_FAIXA_ETARIA", "grupo_etario", "faixa", "grupo"],
        "faixa etária",
    )
    coluna_contagem = coluna_contagem or _resolver_coluna(
        dados, ["n_participantes", "n_inscritos", "n", "frequencia", "quantidade",
               "participantes", "contagem"],
        "contagem de participantes",
    )
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados["participantes"] = pd.to_numeric(dados[coluna_contagem], errors="coerce")
    dados["faixa_etaria_codigo"] = dados[coluna_faixa].astype("string").str.strip()
    dados["faixa_etaria"] = normalizar_faixa_etaria(dados[coluna_faixa])
    if coluna_sexo is None:
        coluna_sexo = next((c for c in ["sexo", "TP_SEXO"] if c in dados.columns), None)
    if coluna_sexo:
        dados["sexo"] = _normalizar_sexo(dados[coluna_sexo])
    return dados


def calcular_distribuicao_idade(dados: pd.DataFrame, por_sexo: bool = False) -> pd.DataFrame:
    """Calcula frequência e percentual por faixa etária, anual e opcionalmente por sexo."""
    chaves = ["ano", "faixa_etaria"]
    if por_sexo:
        validar_colunas(dados, ["sexo"], "participação por idade")
        chaves.append("sexo")
    validar_colunas(dados, chaves + ["participantes"], "participação por idade")
    base = dados.copy()
    base["participantes"] = pd.to_numeric(base["participantes"], errors="coerce")
    agregado = base.groupby(chaves, as_index=False, dropna=False, observed=False).agg(
        participantes=("participantes", lambda s: s.sum(min_count=1))
    )
    denominadores = ["ano"] + (["sexo"] if por_sexo else [])
    agregado["total_referencia"] = agregado.groupby(
        denominadores, dropna=False
    )["participantes"].transform("sum")
    agregado["percentual"] = (
        agregado["participantes"]
        .div(agregado["total_referencia"].where(agregado["total_referencia"].gt(0)))
        * 100
    )
    return agregado.sort_values(chaves).reset_index(drop=True)


def preparar_desempenho_idade_dsp(
    dsp: pd.DataFrame,
    referencia: str = "ESC",
) -> pd.DataFrame:
    """
    Prepara desempenho por faixa etária a partir de dsp.

    A base é municipal, por sexo, faixa etária e disciplina. As estatísticas
    municipais não reconstroem diretamente a distribuição estadual individual.
    """
    obrigatorias = [
        "ano", "sexo", "faixa_etaria", "disciplina", "n_participantes",
        "n_validos", "media", "mediana", "std", "q1", "q3",
        "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO",
    ]
    validar_colunas(dsp, obrigatorias, "dsp")
    dados = filtrar_referencia(dsp, referencia).copy()
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    for c in ["n_participantes", "n_validos", "media", "media_positivas",
              "mediana", "std", "q1", "q3"]:
        if c in dados.columns:
            dados[c] = pd.to_numeric(dados[c], errors="coerce")
    dados["sexo"] = _normalizar_sexo(dados["sexo"])
    dados["faixa_etaria_codigo"] = dados["faixa_etaria"].astype("string").str.strip()
    dados["faixa_etaria"] = normalizar_faixa_etaria(dados["faixa_etaria"])
    dados = dados.loc[dados["n_validos"].gt(0)].copy()
    dados["iqr_municipal"] = dados["q3"] - dados["q1"]
    return dados.sort_values(
        ["ano", "disciplina", "faixa_etaria", "sexo", "NO_MUNICIPIO_TERRITORIO"]
    ).reset_index(drop=True)


def agregar_desempenho_idade_dsp(dados: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega médias ponderadas por n_validos, combinando sexos.

    Medianas, quartis e desvios-padrão são resumos das estatísticas municipais,
    não estatísticas individuais estaduais.
    """
    chaves = ["ano", "disciplina", "faixa_etaria"]
    validar_colunas(
        dados, chaves + ["n_validos", "media", "mediana", "std", "q1", "q3",
                         "CO_MUNICIPIO_TERRITORIO"],
        "dsp por idade",
    )
    base = dados.copy()
    base["_soma_ponderada"] = base["media"] * base["n_validos"]
    resultado = base.groupby(chaves, as_index=False, dropna=False, observed=False).agg(
        soma_ponderada=("_soma_ponderada", "sum"),
        n_validos=("n_validos", "sum"),
        n_municipios=("CO_MUNICIPIO_TERRITORIO", "nunique"),
        mediana_municipal_mediana=("mediana", "median"),
        q1_das_medianas_municipais=("mediana", lambda s: s.quantile(.25)),
        q3_das_medianas_municipais=("mediana", lambda s: s.quantile(.75)),
        std_municipal_mediana=("std", "median"),
        q1_municipal_mediana=("q1", "median"),
        q3_municipal_mediana=("q3", "median"),
    )
    resultado["media_ponderada"] = resultado["soma_ponderada"] / resultado["n_validos"]
    resultado["iqr_municipal_mediana"] = (
        resultado["q3_municipal_mediana"] - resultado["q1_municipal_mediana"]
    )
    return resultado.drop(columns="soma_ponderada").sort_values(chaves).reset_index(drop=True)


def resumir_dispersao_idade_dsp(dados: pd.DataFrame) -> pd.DataFrame:
    """Resume desvio-padrão e IQR municipais por ano, disciplina e faixa etária."""
    chaves = ["ano", "disciplina", "faixa_etaria"]
    return dados.groupby(chaves, as_index=False, dropna=False, observed=False).agg(
        std_municipal_mediana=("std", "median"),
        iqr_municipal_mediana=("iqr_municipal", "median"),
        n_municipios=("CO_MUNICIPIO_TERRITORIO", "nunique"),
        n_validos=("n_validos", "sum"),
    ).sort_values(chaves).reset_index(drop=True)




def calcular_distribuicao_idade_sexo_dsp(dados: pd.DataFrame) -> pd.DataFrame:
    """Calcula I05 por disciplina, sexo e faixa etária usando inscritos."""

    chaves = [
        "ano",
        "CO_MUNICIPIO_TERRITORIO",
        "NO_MUNICIPIO_TERRITORIO",
        "sexo",
        "faixa_etaria",
        "disciplina",
    ]

    validar_colunas(
        dados,
        chaves + ["n_participantes"],
        "dsp para I05",
    )

    base = dados[chaves + ["n_participantes"]].copy()

    base["n_participantes"] = pd.to_numeric(
        base["n_participantes"],
        errors="coerce",
    )

    # Consolida as categorias originais que foram agrupadas
    # nas cinco faixas etárias do projeto.
    municipal = (
        base.groupby(
            chaves,
            as_index=False,
            dropna=False,
            observed=False,
        )
        .agg(
            participantes=(
                "n_participantes",
                lambda s: s.sum(min_count=1),
            )
        )
    )

    # Agrega os municípios, mantendo as disciplinas separadas.
    anual = (
        municipal.groupby(
            ["ano", "sexo", "faixa_etaria", "disciplina"],
            as_index=False,
            dropna=False,
            observed=False,
        )
        .agg(
            participantes=(
                "participantes",
                lambda s: s.sum(min_count=1),
            )
        )
    )

    # Percentual dentro de cada combinação ano-sexo-disciplina.
    anual["total_inscritos_grupo"] = (
        anual.groupby(
            ["ano", "sexo", "disciplina"],
            dropna=False,
            observed=False,
        )["participantes"].transform("sum")
    )

    anual["percentual"] = (
        anual["participantes"]
        .div(
            anual["total_inscritos_grupo"].where(
                anual["total_inscritos_grupo"].gt(0)
            )
        )
        * 100
    )

    return anual.sort_values(
        ["ano", "disciplina", "sexo", "faixa_etaria"]
    ).reset_index(drop=True)



# =============================================================================
# EIXO 5 — DESIGUALDADE TERRITORIAL E DESEMPENHO MUNICIPAL
# =============================================================================

def preparar_desempenho_territorial_dsp(
    dsp: pd.DataFrame,
    referencia: str = "ESC",
    n_minimo_participantes: int = 100,
    anos_inicio_comparavel: int = 2002,
    painel: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Consolida o DSP em uma observação por município/ano/disciplina.

    As linhas de sexo/faixa etária são combinadas por média ponderada por
    n_validos. Quando painel é fornecido, o N total municipal vem do painel,
    evitando somar contagens estratificadas do DSP para aplicar o corte.

    O filtro N>100 é registrado como elegibilidade, sem eliminar a base bruta.
    1998–2001 permanecem disponíveis para descrição exploratória.
    """
    obrigatorias = [
        "ano", "disciplina", "n_validos", "media",
        "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO",
    ]
    validar_colunas(dsp, obrigatorias, "dsp para Eixo 5")
    dados = filtrar_referencia(dsp, referencia).copy()
    for col in ["ano", "n_validos", "media"]:
        dados[col] = pd.to_numeric(dados[col], errors="coerce")
    if "n_participantes" in dados:
        dados["n_participantes_dsp"] = pd.to_numeric(
            dados["n_participantes"], errors="coerce"
        )
    else:
        dados["n_participantes_dsp"] = np.nan

    dados = dados.dropna(subset=[
        "ano", "disciplina", "CO_MUNICIPIO_TERRITORIO", "n_validos", "media"
    ])
    dados = dados.loc[dados["n_validos"].gt(0)].copy()
    chaves = [
        "ano", "CO_MUNICIPIO_TERRITORIO",
        "NO_MUNICIPIO_TERRITORIO", "disciplina",
    ]
    dados["_soma_ponderada"] = dados["media"] * dados["n_validos"]
    municipal = dados.groupby(
        chaves, as_index=False, dropna=False, observed=False
    ).agg(
        soma_ponderada=("_soma_ponderada", "sum"),
        n_validos=("n_validos", "sum"),
        n_participantes_dsp=("n_participantes_dsp", "sum"),
        n_estratos=("n_validos", "size"),
    )
    municipal["media_ponderada"] = (
        municipal["soma_ponderada"] / municipal["n_validos"]
    )
    municipal = municipal.drop(columns="soma_ponderada")

    if painel is not None:
        validar_colunas(
            painel,
            ["ano", "CO_MUNICIPIO_TERRITORIO", "n_participantes"],
            "painel para Eixo 5",
        )
        p = filtrar_referencia(painel, referencia).copy()
        p["ano"] = pd.to_numeric(p["ano"], errors="coerce")
        p["n_participantes"] = pd.to_numeric(
            p["n_participantes"], errors="coerce"
        )
        p = p.groupby(
            ["ano", "CO_MUNICIPIO_TERRITORIO"], as_index=False, dropna=False
        ).agg(n_participantes=("n_participantes", "sum"))
        municipal = municipal.merge(
            p, on=["ano", "CO_MUNICIPIO_TERRITORIO"], how="left",
            validate="many_to_one",
        )
    else:
        municipal["n_participantes"] = municipal["n_participantes_dsp"]

    municipal["n_minimo_participantes"] = n_minimo_participantes
    municipal["elegivel_n100"] = municipal["n_participantes"].gt(
        n_minimo_participantes
    )
    municipal["periodo_inicial_baixa_adesao"] = (
        municipal["ano"].lt(anos_inicio_comparavel)
    )
    municipal["elegivel_analise_principal"] = (
        municipal["elegivel_n100"]
        & municipal["ano"].ge(anos_inicio_comparavel)
    )
    return municipal.sort_values(chaves).reset_index(drop=True)


def calcular_indicadores_desigualdade_territorial(
    desempenho_municipal: pd.DataFrame,
    usar_elegiveis: bool = True,
) -> pd.DataFrame:
    """Calcula dispersão das médias municipais por ano e disciplina."""
    validar_colunas(
        desempenho_municipal,
        ["ano", "disciplina", "CO_MUNICIPIO_TERRITORIO", "media_ponderada",
         "n_participantes"],
        "desempenho municipal",
    )
    base = desempenho_municipal.copy()
    if usar_elegiveis and "elegivel_analise_principal" in base:
        base = base.loc[base["elegivel_analise_principal"]].copy()
    resultados = []
    for (ano, disciplina), g in base.groupby(
        ["ano", "disciplina"], dropna=False, observed=False
    ):
        x = pd.to_numeric(g["media_ponderada"], errors="coerce").dropna()
        x = x[np.isfinite(x)]
        if x.empty:
            continue
        q10, q25, mediana, q75, q90 = x.quantile([.10, .25, .50, .75, .90])
        media = x.mean()
        std = x.std(ddof=1) if len(x) > 1 else np.nan
        resultados.append({
            "ano": ano, "disciplina": disciplina,
            "n_municipios": int(x.size),
            "media_municipal_media": float(media),
            "mediana_municipal": float(mediana),
            "std_municipal": float(std),
            "cv_municipal_pct": float(std / media * 100) if media != 0 and pd.notna(std) else np.nan,
            "q10": float(q10), "q25": float(q25), "q75": float(q75), "q90": float(q90),
            "iqr": float(q75 - q25),
            "p90_p10": float(q90 - q10),
            "gini_medias_municipais": _gini(x.to_numpy()),
            "minimo": float(x.min()), "maximo": float(x.max()),
        })
    return pd.DataFrame(resultados).sort_values(
        ["disciplina", "ano"]
    ).reset_index(drop=True)


def calcular_estabilidade_municipal(
    desempenho_municipal: pd.DataFrame,
    ano_inicio: int = 2002,
    ano_fim: int | None = None,
    cobertura_minima: float = 0.70,
    minimo_anos: int = 10,
) -> pd.DataFrame:
    """
    Mede estabilidade temporal por município/disciplina usando CV temporal,
    desvio-padrão, amplitude e inclinação linear das médias anuais.
    Exige cobertura mínima no período; ordenação por menor CV.
    """
    validar_colunas(
        desempenho_municipal,
        ["ano", "disciplina", "CO_MUNICIPIO_TERRITORIO",
         "NO_MUNICIPIO_TERRITORIO", "media_ponderada",
         "elegivel_analise_principal"],
        "desempenho municipal",
    )
    base = desempenho_municipal.loc[
        desempenho_municipal["elegivel_analise_principal"]
        & desempenho_municipal["ano"].ge(ano_inicio)
    ].copy()
    if ano_fim is None:
        ano_fim = int(base["ano"].max())
    base = base.loc[base["ano"].le(ano_fim)]
    anos_esperados = max(1, ano_fim - ano_inicio + 1)
    linhas = []
    chaves = ["CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO", "disciplina"]
    for chave, g in base.groupby(chaves, dropna=False, observed=False):
        g = g.sort_values("ano")
        x = g["media_ponderada"].astype(float).to_numpy()
        anos = g["ano"].astype(float).to_numpy()
        n = len(x)
        cobertura = n / anos_esperados
        if n < minimo_anos or cobertura < cobertura_minima:
            continue
        media = float(np.mean(x))
        std = float(np.std(x, ddof=1)) if n > 1 else np.nan
        slope = float(np.polyfit(anos, x, 1)[0]) if n > 1 else np.nan
        linhas.append({
            "CO_MUNICIPIO_TERRITORIO": chave[0],
            "NO_MUNICIPIO_TERRITORIO": chave[1],
            "disciplina": chave[2],
            "ano_inicio": int(np.min(anos)),
            "ano_fim": int(np.max(anos)),
            "n_anos": n,
            "cobertura_periodo_pct": cobertura * 100,
            "media_periodo": media,
            "std_temporal": std,
            "cv_temporal_pct": std / media * 100 if media else np.nan,
            "amplitude_temporal": float(np.max(x) - np.min(x)),
            "inclinacao_pontos_ano": slope,
        })
    return pd.DataFrame(linhas).sort_values(
        ["disciplina", "cv_temporal_pct"]
    ).reset_index(drop=True)


def calcular_evolucao_desempenho_municipal(
    desempenho_municipal: pd.DataFrame,
    ano_inicial: int = 2002,
    ano_final: int | None = None,
) -> pd.DataFrame:
    """Compara médias no primeiro e último ano elegíveis comuns por município/disciplina."""
    validar_colunas(
        desempenho_municipal,
        ["ano", "disciplina", "CO_MUNICIPIO_TERRITORIO",
         "NO_MUNICIPIO_TERRITORIO", "media_ponderada",
         "n_participantes", "elegivel_analise_principal"],
        "desempenho municipal",
    )
    base = desempenho_municipal.loc[
        desempenho_municipal["elegivel_analise_principal"]
        & desempenho_municipal["ano"].ge(ano_inicial)
    ].copy()
    if ano_final is None:
        ano_final = int(base["ano"].max())
    chaves = ["CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO", "disciplina"]
    inicial = base.loc[base["ano"].eq(ano_inicial), chaves + [
        "media_ponderada", "n_participantes"
    ]].rename(columns={
        "media_ponderada": "media_inicial",
        "n_participantes": "n_participantes_inicial",
    })
    final = base.loc[base["ano"].eq(ano_final), chaves + [
        "media_ponderada", "n_participantes"
    ]].rename(columns={
        "media_ponderada": "media_final",
        "n_participantes": "n_participantes_final",
    })
    resultado = inicial.merge(final, on=chaves, how="inner")
    resultado["variacao_pontos"] = resultado["media_final"] - resultado["media_inicial"]
    resultado["variacao_percentual"] = np.where(
        resultado["media_inicial"].ne(0),
        resultado["variacao_pontos"] / resultado["media_inicial"] * 100,
        np.nan,
    )
    resultado["ano_inicial"] = ano_inicial
    resultado["ano_final"] = ano_final
    return resultado.sort_values(
        ["disciplina", "variacao_pontos"], ascending=[True, False]
    ).reset_index(drop=True)


def calcular_ranking_territorial(
    desempenho_municipal: pd.DataFrame,
    ano: int | None = None,
    top_n: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna ranking anual completo e síntese de frequência no top N."""
    validar_colunas(
        desempenho_municipal,
        ["ano", "disciplina", "CO_MUNICIPIO_TERRITORIO",
         "NO_MUNICIPIO_TERRITORIO", "media_ponderada",
         "n_participantes", "elegivel_analise_principal"],
        "desempenho municipal",
    )
    base = desempenho_municipal.loc[
        desempenho_municipal["elegivel_analise_principal"]
    ].copy()
    if ano is not None:
        base = base.loc[base["ano"].eq(ano)]
    base["ranking"] = base.groupby(
        ["ano", "disciplina"], observed=False
    )["media_ponderada"].rank(method="min", ascending=False)
    base["top_n"] = base["ranking"].le(top_n)
    frequencia = base.loc[base["top_n"]].groupby(
        ["CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO", "disciplina"],
        as_index=False, dropna=False, observed=False
    ).agg(
        anos_no_top_n=("ano", "nunique"),
        media_dos_anos_top=("media_ponderada", "mean"),
        melhor_ranking=("ranking", "min"),
    )
    return (
        base.sort_values(["ano", "disciplina", "ranking"]).reset_index(drop=True),
        frequencia.sort_values(
            ["disciplina", "anos_no_top_n", "media_dos_anos_top"],
            ascending=[True, False, False],
        ).reset_index(drop=True),
    )


def calcular_relacao_participacao_desempenho(
    desempenho_municipal: pd.DataFrame,
) -> pd.DataFrame:
    """Correlaciona número de participantes e média municipal por ano/disciplina."""
    validar_colunas(
        desempenho_municipal,
        ["ano", "disciplina", "n_participantes", "media_ponderada",
         "elegivel_analise_principal"],
        "desempenho municipal",
    )
    base = desempenho_municipal.loc[
        desempenho_municipal["elegivel_analise_principal"]
    ].copy()
    linhas = []
    for (ano, disciplina), g in base.groupby(
        ["ano", "disciplina"], dropna=False, observed=False
    ):
        g = g[["n_participantes", "media_ponderada"]].dropna()
        if len(g) < 3:
            continue
        n = g["n_participantes"]
        media = g["media_ponderada"]
        pearson = n.corr(media, method="pearson") if n.nunique() > 1 and media.nunique() > 1 else np.nan
        spearman = n.corr(media, method="spearman") if n.nunique() > 1 and media.nunique() > 1 else np.nan
        log_n = np.log1p(n)
        log_pearson = log_n.corr(media) if log_n.nunique() > 1 and media.nunique() > 1 else np.nan
        linhas.append({
            "ano": ano, "disciplina": disciplina,
            "n_municipios": len(g),
            "pearson_n_media": pearson,
            "spearman_n_media": spearman,
            "pearson_log_n_media": log_pearson,
        })
    return pd.DataFrame(linhas).sort_values(
        ["disciplina", "ano"]
    ).reset_index(drop=True)


# =============================================================================
# EIXO 6 — DISTRIBUIÇÃO E DESIGUALDADE DO DESEMPENHO
# Fontes: painel (série municipal de desempenho), grupo (recortes sociais/escolares),
# dsp (detalhamento sexo/faixa etária, 2001-2023) e faixa (composição etária).

_DISCIPLINAS_PAINEL_EIXO6 = {
    "redacao": "REDACAO", "objetiva": "OBJETIVA", "cn": "CN",
    "ch": "CH", "lc": "LC", "mt": "MT",
}


def _normalizar_escala_eixo6(dados: pd.DataFrame) -> pd.DataFrame:
    """Padroniza notas da estrutura antiga (0-100) para 0-1000, sem ligar séries distintas."""
    dados = dados.copy()
    antigas = dados["ano"].lt(2009) & dados["disciplina"].isin(["OBJETIVA", "REDACAO"])
    cols = [c for c in ["media", "media_positivas", "mediana", "std", "q1", "q3"] if c in dados]
    dados.loc[antigas, cols] = dados.loc[antigas, cols] * 10
    dados["periodo_metodologico"] = np.where(
        dados["ano"].lt(2009), "1998-2008_estrutura_antiga", "2009-2025_novo_enem"
    )
    return dados


def preparar_desempenho_municipal_eixo6(
    painel: pd.DataFrame, referencia: str = "ESC"
) -> pd.DataFrame:
    """Converte estatísticas disciplinares do painel (wide) para formato longo."""
    validar_colunas(painel, ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO"], "painel")
    base = filtrar_referencia(painel, referencia).copy()
    base["ano"] = pd.to_numeric(base["ano"], errors="coerce")
    linhas = []
    for sufixo, disciplina in _DISCIPLINAS_PAINEL_EIXO6.items():
        col_n = f"n_validos_{sufixo}"
        if col_n not in base.columns:
            continue
        for _, r in base.iterrows():
            n = pd.to_numeric(r.get(col_n), errors="coerce")
            if pd.isna(n) or n <= 0:
                continue
            item = {
                "ano": r["ano"], "disciplina": disciplina,
                "CO_MUNICIPIO_TERRITORIO": r["CO_MUNICIPIO_TERRITORIO"],
                "NO_MUNICIPIO_TERRITORIO": r["NO_MUNICIPIO_TERRITORIO"],
                "n_validos": n,
            }
            for metrica in ["media", "media_positivas", "mediana", "std", "q1", "q3"]:
                item[metrica] = pd.to_numeric(r.get(f"{metrica}_{sufixo}"), errors="coerce")
            item["n_zeros"] = pd.to_numeric(r.get(f"n_zeros_{sufixo}"), errors="coerce")
            linhas.append(item)
    if not linhas:
        raise ValueError("Painel não contém colunas disciplinares n_validos_* compatíveis.")
    dados = pd.DataFrame(linhas).dropna(subset=["ano", "media"])
    dados["ano"] = dados["ano"].astype(int)
    dados = _normalizar_escala_eixo6(dados)
    dados["iqr_municipal"] = dados["q3"] - dados["q1"]
    return dados.sort_values(["ano", "disciplina", "NO_MUNICIPIO_TERRITORIO"]).reset_index(drop=True)


def resumir_distribuicao_municipal_eixo6(dados: pd.DataFrame) -> pd.DataFrame:
    """Série anual/disciplinar: média e DP combinados entre municípios; quartis municipais identificados."""
    validar_colunas(dados, ["ano", "disciplina", "n_validos", "media", "std", "mediana", "q1", "q3"], "painel longo")
    linhas = []
    for (ano, disc), g in dados.groupby(["ano", "disciplina"], observed=False):
        g = g.loc[g.n_validos.gt(0)].copy()
        n = pd.to_numeric(g.n_validos, errors="coerce")
        m = pd.to_numeric(g.media, errors="coerce")
        ok = n.notna() & m.notna()
        n, m, g = n[ok], m[ok], g.loc[ok]
        total = n.sum()
        media = float((n*m).sum()/total) if total else np.nan
        s = pd.to_numeric(g["std"], errors="coerce")
        std_completo = not ((n > 1) & s.isna()).any()
        s_ajustado = s.where(n > 1, 0).fillna(0)
        within = (((n-1).clip(lower=0)) * s_ajustado.pow(2)).sum()
        between = (n * (m-media).pow(2)).sum() if total else np.nan
        std = float(np.sqrt((within+between)/(total-1))) if total > 1 and std_completo else np.nan
        nz = pd.to_numeric(g.n_zeros, errors="coerce") if "n_zeros" in g else pd.Series(0, index=g.index)
        nz = nz.fillna(0).clip(lower=0)
        np_ = (n-nz).clip(lower=0)
        mp = pd.to_numeric(g.media_positivas, errors="coerce")
        valid_mp = mp.notna() & np_.gt(0)
        media_pos = float((mp[valid_mp]*np_[valid_mp]).sum()/np_[valid_mp].sum()) if valid_mp.any() else np.nan
        q1, q3 = pd.to_numeric(g.q1, errors="coerce"), pd.to_numeric(g.q3, errors="coerce")
        med = pd.to_numeric(g.mediana, errors="coerce")
        linhas.append({
            "ano": int(ano), "disciplina": disc, "n_municipios": int(g.CO_MUNICIPIO_TERRITORIO.nunique()),
            "n_validos": int(total), "n_zeros": int(nz.sum()),
            "pct_zeros": float(nz.sum()/total*100) if total else np.nan,
            "media_ponderada": media, "media_ponderada_sem_zero": media_pos,
            "std_combinado_aprox": std,
            "mediana_das_medianas_municipais": float(med.median()) if med.notna().any() else np.nan,
            "q1_mediano_municipal": float(q1.median()) if q1.notna().any() else np.nan,
            "q3_mediano_municipal": float(q3.median()) if q3.notna().any() else np.nan,
            "iqr_mediano_municipal": float((q3-q1).median()) if (q1.notna()&q3.notna()).any() else np.nan,
            "p25_medias_municipais": float(m.quantile(.25)),
            "p75_medias_municipais": float(m.quantile(.75)),
            "iqr_medias_municipais": float(m.quantile(.75)-m.quantile(.25)),
            "periodo_metodologico": "1998-2008_estrutura_antiga" if int(ano)<2009 else "2009-2025_novo_enem",
        })
    return pd.DataFrame(linhas).sort_values(["disciplina", "ano"]).reset_index(drop=True)


def preparar_grupos_desempenho_eixo6(grupo: pd.DataFrame, referencia: str = "ESC") -> pd.DataFrame:
    """Prepara estatísticas por sexo, faixa etária e dependência escolar."""
    obrig = ["ano", "tipo_grupo", "grupo", "disciplina", "n_validos", "n_zeros", "media", "media_positivas", "mediana", "std", "q1", "q3", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO"]
    validar_colunas(grupo, obrig, "grupo")
    d = filtrar_referencia(grupo, referencia).copy()
    for c in ["ano", "n_validos", "n_zeros", "media", "media_positivas", "mediana", "std", "q1", "q3"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["ano", "disciplina", "n_validos", "media"])
    d = d.loc[d.n_validos.gt(0)].copy()
    d["ano"] = d.ano.astype(int)
    d["tipo_grupo"] = d.tipo_grupo.astype("string").str.upper().str.strip()
    d["grupo_original"] = d.grupo.astype("string").str.strip()
    d["grupo"] = d["grupo_original"]
    mask_faixa = d["tipo_grupo"].eq("FAIXA_ETARIA")
    d.loc[mask_faixa, "grupo"] = _normalizar_faixa_etaria_eixo6(
        d.loc[mask_faixa, "grupo_original"]
    ).astype("string")
    return _normalizar_escala_eixo6(d)


def resumir_grupos_desempenho_eixo6(dados: pd.DataFrame) -> pd.DataFrame:
    """Agrega médias ponderadas e resume quartis dos registros municipais por categoria."""
    chaves = ["ano", "tipo_grupo", "grupo", "disciplina"]
    linhas=[]
    for chave,g in dados.groupby(chaves, dropna=False, observed=False):
        n=g.n_validos.astype(float); m=g.media.astype(float); total=n.sum()
        nz=g.n_zeros.fillna(0).clip(lower=0)
        np_= (n-nz).clip(lower=0)
        mp=g.media_positivas
        valid=mp.notna() & np_.gt(0)
        med=g.mediana.dropna(); q1=g.q1.dropna(); q3=g.q3.dropna()
        linhas.append(dict(zip(chaves,chave)) | {
            "n_municipios":g.CO_MUNICIPIO_TERRITORIO.nunique(), "n_validos":int(total), "n_zeros":int(nz.sum()),
            "pct_zeros":float(nz.sum()/total*100) if total else np.nan,
            "media_ponderada":float((n*m).sum()/total) if total else np.nan,
            "media_ponderada_sem_zero":float((mp[valid]*np_[valid]).sum()/np_[valid].sum()) if valid.any() else np.nan,
            "mediana_das_medianas_municipais":float(med.median()) if len(med) else np.nan,
            "q1_mediano_municipal":float(q1.median()) if len(q1) else np.nan,
            "q3_mediano_municipal":float(q3.median()) if len(q3) else np.nan,
            "iqr_mediano_municipal":float((g.q3-g.q1).median()),
            "std_mediano_municipal":float(g.loc[g["std"].notna(),"std"].median()) if g["std"].notna().any() else np.nan,
        })
    return pd.DataFrame(linhas).sort_values(chaves).reset_index(drop=True)


def calcular_disparidade_social_municipal_eixo6(grupos: pd.DataFrame, painel_longo: pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame]:
    """D04: compara dispersão territorial com amplitude social dentro de cada município."""
    # Dispersão territorial das médias municipais (painel).
    terr=[]
    for (ano,disc),g in painel_longo.groupby(["ano","disciplina"], observed=False):
        x=g.media.dropna()
        if len(x): terr.append({"ano":ano,"disciplina":disc,"dimensao":"territorial_medias_municipais","n_municipios":len(x),"mediana_amplitude_ou_disp":float(x.std(ddof=1)) if len(x)>1 else np.nan,"q25":x.quantile(.25),"q75":x.quantile(.75),"iqr":x.quantile(.75)-x.quantile(.25),"p90_p10":x.quantile(.90)-x.quantile(.10)})
    # Diferença máximo-mínimo entre categorias sociais/escolares dentro de cada município.
    d=grupos.loc[grupos.tipo_grupo.isin(["SEXO","FAIXA_ETARIA","ESCOLA"])].copy()
    d["media"] = pd.to_numeric(d.media,errors="coerce")
    chaves_cat=["ano","disciplina","tipo_grupo","CO_MUNICIPIO_TERRITORIO","NO_MUNICIPIO_TERRITORIO","grupo"]
    d["_soma_media_n"] = d["media"] * d["n_validos"]
    cat=(d.groupby(chaves_cat,as_index=False,dropna=False,observed=False)
           .agg(_soma_media_n=("_soma_media_n","sum"), n_validos=("n_validos","sum")))
    cat["media_categoria"] = cat["_soma_media_n"] / cat["n_validos"].where(cat["n_validos"].gt(0))
    cat=cat.drop(columns="_soma_media_n")
    social=[]
    for (ano,disc,tipo),g in cat.groupby(["ano","disciplina","tipo_grupo"],observed=False):
        for mun,gm in g.groupby("CO_MUNICIPIO_TERRITORIO",dropna=False):
            vals=gm.media_categoria.dropna()
            if len(vals)>=2:
                social.append({"ano":ano,"disciplina":disc,"dimensao":f"amplitude_interna_{tipo.lower()}","CO_MUNICIPIO_TERRITORIO":mun,"n_categorias":len(vals),"amplitude_categorias":float(vals.max()-vals.min())})
    s=pd.DataFrame(social)
    if not s.empty:
        for (ano,disc,dim),g in s.groupby(["ano","disciplina","dimensao"],observed=False):
            x=g.amplitude_categorias
            terr.append({"ano":ano,"disciplina":disc,"dimensao":dim,"n_municipios":len(x),"mediana_amplitude_ou_disp":x.median(),"q25":x.quantile(.25),"q75":x.quantile(.75),"iqr":x.quantile(.75)-x.quantile(.25),"p90_p10":x.quantile(.90)-x.quantile(.10)})
    return cat, pd.DataFrame(terr).sort_values(["disciplina","dimensao","ano"]).reset_index(drop=True)


def preparar_dsp_detalhado_eixo6(dsp: pd.DataFrame, referencia: str = "ESC") -> pd.DataFrame:
    """Prepara DSP por sexo/faixa etária para auditoria e detalhamento 2001-2023."""
    obrig=["ano","sexo","faixa_etaria","disciplina","n_validos","n_zeros","media","mediana","std","q1","q3","CO_MUNICIPIO_TERRITORIO"]
    validar_colunas(dsp,obrig,"dsp")
    d=filtrar_referencia(dsp,referencia).copy()
    for c in ["ano","n_validos","n_zeros","media","media_positivas","mediana","std","q1","q3"]:
        if c in d: d[c]=pd.to_numeric(d[c],errors="coerce")
    d=d.dropna(subset=["ano","n_validos","media"]); d=d.loc[d.n_validos.gt(0)].copy(); d["ano"]=d.ano.astype(int)
    d["faixa_etaria_original"]=d.faixa_etaria.astype("string").str.strip()
    d["faixa_etaria"]=_normalizar_faixa_etaria_eixo6(d["faixa_etaria_original"])
    return _normalizar_escala_eixo6(d)


def resumir_composicao_etaria_eixo6(faixa: pd.DataFrame, referencia: str = "ESC") -> pd.DataFrame:
    """Resume quantidade e participação relativa por faixa etária; não contém notas."""
    obrig=["ano","TP_FAIXA_ETARIA","n_participantes","CO_MUNICIPIO_TERRITORIO"]
    validar_colunas(faixa,obrig,"faixa")
    d=filtrar_referencia(faixa,referencia).copy()
    d["ano"]=pd.to_numeric(d.ano,errors="coerce"); d["n_participantes"]=pd.to_numeric(d.n_participantes,errors="coerce")
    d=d.dropna(subset=["ano","n_participantes"])
    d["faixa_etaria_codigo"]=d["TP_FAIXA_ETARIA"].astype("string").str.strip()
    d["faixa_etaria"]=_normalizar_faixa_etaria_eixo6(d["TP_FAIXA_ETARIA"])
    r=d.groupby(["ano","faixa_etaria"],as_index=False,dropna=False,observed=False).agg(n_participantes=("n_participantes","sum"),n_municipios=("CO_MUNICIPIO_TERRITORIO","nunique"))
    r["total_ano"]=r.groupby("ano").n_participantes.transform("sum")
    r["pct_participantes"]=r.n_participantes.div(r.total_ano.where(r.total_ano.gt(0)))*100
    return r.sort_values(["ano","faixa_etaria"], key=lambda col: col.map({v:i for i,v in enumerate(ORDEM_FAIXAS)}).fillna(99) if col.name == "faixa_etaria" else col).reset_index(drop=True)


def auditar_fontes_eixo6(painel: pd.DataFrame, faixa: pd.DataFrame, grupo: pd.DataFrame, dsp: pd.DataFrame, referencia: str="ESC") -> pd.DataFrame:
    """Auditoria de cobertura temporal, territorial e dimensional das quatro fontes."""
    linhas=[]
    for nome,df in [("painel",painel),("faixa",faixa),("grupo",grupo),("dsp",dsp)]:
        d=filtrar_referencia(df,referencia)
        anos=pd.to_numeric(d.ano,errors="coerce").dropna()
        linhas.append({"fonte":nome,"linhas":len(d),"anos_inicio":int(anos.min()) if len(anos) else np.nan,"anos_fim":int(anos.max()) if len(anos) else np.nan,"n_anos":int(anos.nunique()),"n_municipios":d.CO_MUNICIPIO_TERRITORIO.nunique() if "CO_MUNICIPIO_TERRITORIO" in d else np.nan,"disciplinas":d.disciplina.nunique() if "disciplina" in d else np.nan,"dimensoes_grupo":", ".join(sorted(d.tipo_grupo.dropna().astype(str).str.upper().unique())) if "tipo_grupo" in d else "não se aplica"})
    return pd.DataFrame(linhas)


# -----------------------------------------------------------------------------
# EIXO 7 — RELAÇÕES ENTRE PARTICIPAÇÃO, PERFIL E DESEMPENHO
# Funções adicionadas sem alterar as funções existentes dos Eixos 1–6.
# -----------------------------------------------------------------------------

def preparar_painel_eixo7(painel: pd.DataFrame, referencia: str = "ESC") -> pd.DataFrame:
    """Converte as estatísticas disciplinares do painel para município-ano-disciplina.

    Preserva a escala recebida da fonte: não multiplica notas históricas.
    """
    validar_colunas(painel, ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO"], "painel")
    base = filtrar_referencia(painel, referencia).copy()
    base["ano"] = pd.to_numeric(base["ano"], errors="coerce")
    linhas = []
    for sufixo, disciplina in _DISCIPLINAS_PAINEL_EIXO6.items():
        col_n = f"n_validos_{sufixo}"
        if col_n not in base.columns:
            continue
        for _, r in base.iterrows():
            n = pd.to_numeric(r.get(col_n), errors="coerce")
            media = pd.to_numeric(r.get(f"media_{sufixo}"), errors="coerce")
            if pd.isna(n) or n <= 0 or pd.isna(media):
                continue
            linhas.append({
                "ano": int(r["ano"]), "disciplina": disciplina,
                "CO_MUNICIPIO_TERRITORIO": r["CO_MUNICIPIO_TERRITORIO"],
                "NO_MUNICIPIO_TERRITORIO": r["NO_MUNICIPIO_TERRITORIO"],
                "n_validos": float(n), "media": float(media),
                "std": pd.to_numeric(r.get(f"std_{sufixo}"), errors="coerce"),
                "q1": pd.to_numeric(r.get(f"q1_{sufixo}"), errors="coerce"),
                "q3": pd.to_numeric(r.get(f"q3_{sufixo}"), errors="coerce"),
            })
    if not linhas:
        raise ValueError("Painel sem colunas disciplinares compatíveis para o Eixo 7.")
    return pd.DataFrame(linhas).sort_values(["ano", "disciplina", "NO_MUNICIPIO_TERRITORIO"]).reset_index(drop=True)


def _correlacoes_eixo7(df: pd.DataFrame, x: str, y: str, chaves: list[str], min_n: int = 8) -> pd.DataFrame:
    """Pearson e Spearman com pares completos e tamanho amostral explícito."""
    from scipy.stats import pearsonr, spearmanr
    linhas = []
    for chave, g in df.groupby(chaves, dropna=False):
        if not isinstance(chave, tuple): chave = (chave,)
        z = g[[x, y]].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        pr = sr = np.nan
        if len(z) >= min_n and z[x].nunique() > 1 and z[y].nunique() > 1:
            pr = float(pearsonr(z[x], z[y]).statistic)
            sr = float(spearmanr(z[x], z[y]).statistic)
        linhas.append(dict(zip(chaves, chave)) | {"n_municipios": len(z), "pearson": pr, "spearman": sr})
    return pd.DataFrame(linhas)


def analisar_r01_crescimento_participacao_desempenho(painel: pd.DataFrame, desempenho: pd.DataFrame,
        ano_inicial: int = 2009, ano_final: int = 2025, referencia: str = "ESC") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Relaciona variação percentual de participantes e variação de média por município.

    Para disciplinas pós-2009, usa anos inicial/final informados. Redação é
    analisada separadamente; OBJETIVA pré-2009 não é conectada às áreas novas.
    """
    validar_colunas(painel, ["ano", "CO_MUNICIPIO_TERRITORIO", "n_participantes"], "painel")
    p = filtrar_referencia(painel, referencia).copy()
    p["ano"] = pd.to_numeric(p.ano, errors="coerce")
    p["n_participantes"] = pd.to_numeric(p.n_participantes, errors="coerce")
    p = p.loc[p.ano.isin([ano_inicial, ano_final])]
    part = p.groupby(["ano", "CO_MUNICIPIO_TERRITORIO"], as_index=False).n_participantes.sum(min_count=1)
    pv = part.pivot(index="CO_MUNICIPIO_TERRITORIO", columns="ano", values="n_participantes")
    if ano_inicial not in pv or ano_final not in pv: raise ValueError("Um dos anos selecionados não existe no painel.")
    pv = pv.dropna(subset=[ano_inicial, ano_final])
    pv = pv.loc[pv[ano_inicial].gt(0)].copy()
    pv["crescimento_participacao_pct"] = (pv[ano_final] / pv[ano_inicial] - 1) * 100
    pv = pv.reset_index()[["CO_MUNICIPIO_TERRITORIO", "crescimento_participacao_pct"]]
    d = desempenho.loc[desempenho.ano.isin([ano_inicial, ano_final])].copy()
    d = d.groupby(["ano", "CO_MUNICIPIO_TERRITORIO", "disciplina"], as_index=False).apply(
        lambda g: pd.Series({"media": np.average(g.media, weights=g.n_validos) if g.n_validos.sum() > 0 else np.nan}),
        include_groups=False).reset_index(drop=True) if False else d
    d = d.groupby(["ano", "CO_MUNICIPIO_TERRITORIO", "disciplina"], as_index=False).agg(
        soma_pond=("media", lambda s: 0), n_validos=("n_validos", "sum"))
    raw = desempenho.loc[desempenho.ano.isin([ano_inicial, ano_final])].copy()
    raw["_pond"] = raw.media * raw.n_validos
    raw = raw.groupby(["ano", "CO_MUNICIPIO_TERRITORIO", "disciplina"], as_index=False).agg(_pond=("_pond", "sum"), n_validos=("n_validos", "sum"))
    raw["media"] = raw._pond / raw.n_validos.where(raw.n_validos.gt(0))
    wide = raw.pivot(index=["CO_MUNICIPIO_TERRITORIO", "disciplina"], columns="ano", values="media").reset_index()
    if ano_inicial not in wide or ano_final not in wide: raise ValueError("Desempenho sem cobertura dos anos selecionados.")
    wide["variacao_media_pontos"] = wide[ano_final] - wide[ano_inicial]
    wide = wide.merge(pv, on="CO_MUNICIPIO_TERRITORIO", how="inner")
    wide["ano_inicial"] = ano_inicial; wide["ano_final"] = ano_final
    wide["periodo"] = f"{ano_inicial}-{ano_final}"
    cor = _correlacoes_eixo7(wide, "crescimento_participacao_pct", "variacao_media_pontos", ["disciplina"], min_n=8)
    return wide, cor


def analisar_r02_rede_publica_desempenho(painel: pd.DataFrame, desempenho: pd.DataFrame,
        referencia: str = "ESC") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Relaciona participação da rede pública e desempenho municipal no mesmo ano."""
    cols = ["ano", "CO_MUNICIPIO_TERRITORIO", "n_escola_federal", "n_escola_estadual", "n_escola_municipal", "n_escola_privada"]
    validar_colunas(painel, cols, "painel")
    p = filtrar_referencia(painel, referencia).copy()
    for c in cols[0:1] + cols[2:]: p[c] = pd.to_numeric(p[c], errors="coerce")
    p["n_publica"] = p[["n_escola_federal", "n_escola_estadual", "n_escola_municipal"]].sum(axis=1, min_count=1)
    p["n_classificada"] = p["n_publica"] + p["n_escola_privada"]
    p["pct_publica"] = p.n_publica / p.n_classificada.where(p.n_classificada.gt(0)) * 100
    comp = p[["ano", "CO_MUNICIPIO_TERRITORIO", "n_publica", "n_escola_privada", "n_classificada", "pct_publica"]]
    d = desempenho[["ano", "CO_MUNICIPIO_TERRITORIO", "disciplina", "media", "n_validos"]].copy()
    d["_pond"] = d.media * d.n_validos
    d = d.groupby(["ano", "CO_MUNICIPIO_TERRITORIO", "disciplina"], as_index=False).agg(_pond=("_pond", "sum"), n_validos=("n_validos", "sum"))
    d["media"] = d._pond / d.n_validos.where(d.n_validos.gt(0))
    base = d.merge(comp, on=["ano", "CO_MUNICIPIO_TERRITORIO"], how="inner")
    base = base.loc[base.n_classificada.gt(0)]
    cor = _correlacoes_eixo7(base, "pct_publica", "media", ["ano", "disciplina"], min_n=8)
    return base, cor


def analisar_r03_sexo_desempenho(painel: pd.DataFrame, desempenho: pd.DataFrame,
        referencia: str = "ESC", ano_final: int = 2023) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Relaciona composição feminina e média geral municipal; média não é exclusiva das mulheres."""
    comp = calcular_participacao_genero_municipal(filtrar_referencia(painel, referencia))
    comp = comp.loc[comp.ano.le(ano_final)].copy()
    d = desempenho.loc[desempenho.ano.le(ano_final)].copy()
    d["_pond"] = d.media * d.n_validos
    d = d.groupby(["ano", "CO_MUNICIPIO_TERRITORIO", "disciplina"], as_index=False).agg(_pond=("_pond", "sum"), n_validos=("n_validos", "sum"))
    d["media_geral"] = d._pond / d.n_validos.where(d.n_validos.gt(0))
    base = d.merge(comp[["ano", "CO_MUNICIPIO_TERRITORIO", "pct_feminino", "sexo_informado"]], on=["ano", "CO_MUNICIPIO_TERRITORIO"], how="inner")
    cor = _correlacoes_eixo7(base, "pct_feminino", "media_geral", ["ano", "disciplina"], min_n=8)
    return base, cor


def analisar_r04_diversidade_etaria_dispersao(faixa: pd.DataFrame, desempenho: pd.DataFrame,
        referencia: str = "ESC") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Relaciona Shannon da composição etária com DP/IQR das notas dentro do município."""
    validar_colunas(faixa, ["ano", "TP_FAIXA_ETARIA", "n_participantes", "CO_MUNICIPIO_TERRITORIO"], "faixa")
    f = filtrar_referencia(faixa, referencia).copy()
    f["ano"] = pd.to_numeric(f.ano, errors="coerce"); f["n_participantes"] = pd.to_numeric(f.n_participantes, errors="coerce")
    f["faixa_etaria"] = _normalizar_faixa_etaria_eixo6(f.TP_FAIXA_ETARIA)
    f = f.dropna(subset=["ano", "n_participantes", "faixa_etaria"])
    f = f.loc[f.n_participantes.ge(0)]
    c = f.groupby(["ano", "CO_MUNICIPIO_TERRITORIO", "faixa_etaria"], as_index=False).n_participantes.sum()
    c["total"] = c.groupby(["ano", "CO_MUNICIPIO_TERRITORIO"]).n_participantes.transform("sum")
    c["p"] = c.n_participantes / c.total.where(c.total.gt(0))
    c["entropia"] = -c.p.where(c.p.gt(0), 1).map(lambda x: x*np.log(x))
    h = c.groupby(["ano", "CO_MUNICIPIO_TERRITORIO"], as_index=False).agg(shannon_etario=("entropia", "sum"), n_faixas=("p", lambda x: int((x>0).sum())), n_participantes_faixa=("total", "max"))
    h["shannon_normalizado"] = h.shannon_etario / np.log(h.n_faixas.where(h.n_faixas.gt(1)))
    d = desempenho.copy()
    d["iqr_interno"] = d.q3 - d.q1
    base = h.merge(d[["ano", "CO_MUNICIPIO_TERRITORIO", "disciplina", "std", "iqr_interno", "n_validos"]], on=["ano", "CO_MUNICIPIO_TERRITORIO"], how="inner")
    linhas=[]
    for (ano,disc),g in base.groupby(["ano","disciplina"]):
        for met in ["std","iqr_interno"]:
            z=g[["shannon_etario",met]].replace([np.inf,-np.inf],np.nan).dropna()
            from scipy.stats import spearmanr, pearsonr
            pr=sr=np.nan
            if len(z)>=8 and z.shannon_etario.nunique()>1 and z[met].nunique()>1:
                pr=float(pearsonr(z.shannon_etario,z[met]).statistic); sr=float(spearmanr(z.shannon_etario,z[met]).statistic)
            linhas.append({"ano":ano,"disciplina":disc,"indicador_dispersao":met,"n_municipios":len(z),"pearson":pr,"spearman":sr})
    return base, pd.DataFrame(linhas)


def analisar_r05_gap_redes_desigualdade(painel: pd.DataFrame, grupo: pd.DataFrame, desempenho: pd.DataFrame,
        referencia: str = "ESC") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Relaciona gap público-privado municipal à posição/desvio da média municipal.

    Usa grupo (tipo_grupo=ESCOLA) e médias originais, sem reescalar notas.
    """
    obrig=["ano","tipo_grupo","grupo","disciplina","n_validos","media","CO_MUNICIPIO_TERRITORIO","NO_MUNICIPIO_TERRITORIO"]
    validar_colunas(grupo, obrig, "grupo")
    g=filtrar_referencia(grupo,referencia).copy()
    g=g.loc[g.tipo_grupo.astype("string").str.upper().eq("ESCOLA")].copy()
    g["dependencia"] = normalizar_dependencia_escolar(g.grupo)
    g["setor"] = np.where(g.dependencia.isin(["FEDERAL","ESTADUAL","MUNICIPAL"]),"PUBLICA",np.where(g.dependencia.eq("PRIVADA"),"PRIVADA",None))
    g["n_validos"] = pd.to_numeric(g.n_validos,errors="coerce"); g["media"] = pd.to_numeric(g.media,errors="coerce")
    g=g.loc[g.setor.notna() & g.n_validos.gt(0) & g.media.notna()].copy(); g["_pond"]=g.media*g.n_validos
    a=g.groupby(["ano","CO_MUNICIPIO_TERRITORIO","NO_MUNICIPIO_TERRITORIO","disciplina","setor"],as_index=False).agg(_pond=("_pond","sum"),n_validos=("n_validos","sum"))
    a["media_setor"]=a._pond/a.n_validos
    w=a.pivot(index=["ano","CO_MUNICIPIO_TERRITORIO","NO_MUNICIPIO_TERRITORIO","disciplina"],columns="setor",values="media_setor").reset_index(); w.columns.name=None
    if "PUBLICA" not in w: w["PUBLICA"]=np.nan
    if "PRIVADA" not in w: w["PRIVADA"]=np.nan
    w["gap_publica_menos_privada"]=w.PUBLICA-w.PRIVADA; w["gap_absoluto"]=w.gap_publica_menos_privada.abs()
    d=desempenho.copy(); d["_pond"]=d.media*d.n_validos
    d=d.groupby(["ano","CO_MUNICIPIO_TERRITORIO","disciplina"],as_index=False).agg(_pond=("_pond","sum"),n_validos=("n_validos","sum"))
    d["media_municipal"]=d._pond/d.n_validos.where(d.n_validos.gt(0))
    d["desvio_territorial"] = d.media_municipal - d.groupby(["ano","disciplina"]).media_municipal.transform("mean")
    base=w.merge(d[["ano","CO_MUNICIPIO_TERRITORIO","disciplina","media_municipal","desvio_territorial"]],on=["ano","CO_MUNICIPIO_TERRITORIO","disciplina"],how="inner")
    base["desvio_territorial_absoluto"]=base.desvio_territorial.abs()
    if base.empty:
        cor = pd.DataFrame(columns=["ano", "disciplina", "n_municipios", "pearson_gap_abs_desvio", "spearman_gap_abs_desvio", "pearson_gap_abs_media", "spearman_gap_abs_media"])
    else:
        c1=_correlacoes_eixo7(base,"gap_absoluto","desvio_territorial_absoluto",["ano","disciplina"],min_n=8).rename(columns={"pearson":"pearson_gap_abs_desvio","spearman":"spearman_gap_abs_desvio"})
        c2=_correlacoes_eixo7(base,"gap_absoluto","media_municipal",["ano","disciplina"],min_n=8).rename(columns={"pearson":"pearson_gap_abs_media","spearman":"spearman_gap_abs_media"})
        cor=c1.merge(c2,on=["ano","disciplina","n_municipios"],how="outer")
    return base, cor

def plotar_resumo_grupos(resumo_grupos):

    configuracoes = {
        "ESCOLA": {
            "titulo": "Desempenho por tipo de escola",
            "ordem": ["ESTADUAL", "FEDERAL", "MUNICIPAL", "PRIVADA"]
        },
        "FAIXA_ETARIA": {
            "titulo": "Desempenho por faixa etária",
            "ordem": ["<17", "17–20", "21–25", "26–40", ">40"]
        },
        "SEXO": {
            "titulo": "Desempenho por sexo",
            "ordem": ["FEMININO", "MASCULINO"]
        }
    }

    disciplinas = [
        "OBJETIVA", "CH", "CN",
        "LC", "MT", "REDACAO"
    ]

    cores = plt.cm.tab10.colors

    for tipo, config in configuracoes.items():

        dados = resumo_grupos[
            resumo_grupos["tipo_grupo"] == tipo
        ].copy()

        dados["media_ponderada_sem_zero"] = pd.to_numeric(
            dados["media_ponderada_sem_zero"],
            errors="coerce"
        )

        fig, axes = plt.subplots(
            2, 3,
            figsize=(15, 8),
            sharex=False
        )

        axes = axes.flatten()

        for ax, disciplina in zip(axes, disciplinas):

            sub = dados[
                dados["disciplina"] == disciplina
            ]

            if sub.empty:
                ax.set_visible(False)
                continue

            for i, grupo in enumerate(config["ordem"]):

                serie = sub[sub["grupo"] == grupo].sort_values("ano")

                if serie.empty:
                    continue

                ax.plot(
                    serie["ano"],
                    serie["media_ponderada_sem_zero"],
                    marker="o",
                    markersize=3,
                    linewidth=1.7,
                    color=cores[i],
                    label=grupo
                )

            ax.set_title(disciplina)
            ax.set_xlabel("Ano")
            ax.set_ylabel("Média")
            ax.grid(alpha=0.25)

        # Legenda única
        handles, labels = axes[0].get_legend_handles_labels()

        fig.legend(
            handles,
            labels,
            loc="lower center",
            ncol=len(config["ordem"]),
            frameon=False
        )

        fig.suptitle(
            config["titulo"],
            fontsize=16  )

        fig.tight_layout(rect=[0, 0.09, 1, 0.98])

        plt.show()


def plotar_comparacao_d04(comparacao_d04):

    dados = comparacao_d04.copy()

    disciplinas = [
        d for d in ["OBJETIVA", "CH", "CN", "LC", "MT", "REDACAO"]
        if d in dados["disciplina"].unique()
    ]

    # ==================================================
    # GRÁFICO 1 — DISPERSÃO TERRITORIAL
    # ==================================================

    territorial = dados[
        dados["dimensao"] == "territorial_medias_municipais"
    ].copy()

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    for ax, disciplina in zip(axes, disciplinas):

        sub = territorial[
            territorial["disciplina"] == disciplina
        ].sort_values("ano")

        if sub.empty:
            ax.set_visible(False)
            continue

        ax.plot(
            sub["ano"],
            sub["iqr"],
            marker="o",
            markersize=3,
            linewidth=1.8,
            label="IQR"
        )

        ax.plot(
            sub["ano"],
            sub["p90_p10"],
            linestyle="--",
            linewidth=1.5,
            label="P90–P10"
        )

        ax.set_title(disciplina)
        ax.set_xlabel("Ano")
        if disciplina in [disciplinas[0], disciplinas[3]]:
            ax.set_ylabel("Dispersão das médias", fontsize=10)
        else:
            ax.set_ylabel("")
        ax.grid(alpha=0.25)

    for ax in axes[len(disciplinas):]:
        ax.set_visible(False)

    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(
        handles, labels,
        loc="lower center",
        ncol=2,
        frameon=False
    )

    fig.suptitle(
        "Dispersão territorial das médias municipais",
        fontsize=16)

    fig.tight_layout(rect=[0, 0.08, 1, 0.95])
    plt.show()

    # ==================================================
    # GRÁFICO 2 — AMPLITUDE ENTRE GRUPOS SOCIAIS
    # ==================================================

    grupos = dados[
        dados["dimensao"] != "territorial_medias_municipais"
    ].copy()

    dimensoes = sorted(grupos["dimensao"].dropna().unique())

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    cores = plt.cm.tab10.colors
    legenda = {}

    for ax, disciplina in zip(axes, disciplinas):

        sub_disciplina = grupos[
            grupos["disciplina"] == disciplina
        ]

        for i, dimensao in enumerate(dimensoes):

            sub = sub_disciplina[
                sub_disciplina["dimensao"] == dimensao
            ].sort_values("ano")

            if sub.empty:
                continue

            cor = cores[i % len(cores)]

            linha, = ax.plot(
                sub["ano"],
                sub["mediana_amplitude_ou_disp"],
                marker="o",
                markersize=3,
                linewidth=1.7,
                color=cor,
                label=dimensao
            )

            ax.fill_between(
                sub["ano"],
                sub["q25"],
                sub["q75"],
                color=cor,
                alpha=0.12
            )

            legenda[dimensao] = linha

        ax.set_title(disciplina)
        ax.set_xlabel("Ano")
        #ax.set_ylabel("Amplitude entre categorias")
        # Mostrar o rótulo somente na primeira coluna
        if disciplina in [disciplinas[0], disciplinas[3]]:
            ax.set_ylabel("Amplitude entre categorias",fontsize=10)
        else:
            ax.set_ylabel("")
        ax.grid(alpha=0.25)

    for ax in axes[len(disciplinas):]:
        ax.set_visible(False)

    if legenda:
        fig.legend(
            legenda.values(),
            legenda.keys(),
            loc="lower center",
            ncol=min(len(legenda), 3),
            frameon=False
        )

    fig.suptitle(
        "Evolução das diferenças entre grupos sociais",
        fontsize=16)

    fig.tight_layout(rect=[0, 0.12, 1, 0.95])
    plt.show()