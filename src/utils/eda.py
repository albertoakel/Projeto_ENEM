#eda.py
from pathlib import Path
import sys
from IPython.display import display




diretorio_atual = Path.cwd().resolve()

if diretorio_atual.name in {"utils"}:
    raiz_projeto = diretorio_atual.parent
else:
    raiz_projeto = diretorio_atual

src_dir = raiz_projeto

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pandas as pd
import numpy as np
from scipy.stats import linregress,spearmanr
import matplotlib.pyplot as plt
import seaborn as sns


# No desenho analítico do projeto:
# 1998–2008 → OBJETIVA
# 2009–2025 → CN, CH, LC, MT
PERIODO_ANTIGO = {"id": "1998_2008",
                  "inicio": 1998,
                  "fim": 2008,
                  "estrutura": "OBJETIVA",
                  "rotulo": "1998–2008"
                 }

PERIODO_NOVO = {"id": "2009_2025",
                "inicio": 2009,
                "fim": 2025,
                "estrutura": "AREAS",
                "rotulo": "2009–2025",
               }

PERIODOS = {PERIODO_ANTIGO["id"]: PERIODO_ANTIGO,
            PERIODO_NOVO["id"]: PERIODO_NOVO}


DISCIPLINAS_ANTIGO = {"media_objetiva": {"nome": "OBJETIVA",
                                         "peso": "n_validos_objetiva",
                                         "redacao": False},
                      "media_redacao": {"nome": "REDACAO",
                                        "peso": "n_validos_redacao",
                                        "redacao": True,
                                        "versao_redacao": "antiga"}}


DISCIPLINAS_NOVO = {"media_redacao": {"nome": "REDACAO",
                                      "peso": "n_validos_redacao",
                                      "redacao": True,
                                      "versao_redacao": "nova"},
                    "media_cn": {"nome": "CN",
                                 "peso": "n_validos_cn",
                                 "redacao": False},
                    "media_ch": {"nome": "CH",
                                 "peso": "n_validos_ch",
                                 "redacao": False},
                    "media_lc": {"nome": "LC",
                                 "peso": "n_validos_lc",
                                 "redacao": False},
                    "media_mt": {"nome": "MT",
                                 "peso": "n_validos_mt",
                                 "redacao": False},
}


ESPECIFICACOES_PERIODO = {
    "1998_2008": DISCIPLINAS_ANTIGO,
    "2009_2025": DISCIPLINAS_NOVO,
}

MAPA_FAIXA_5 = {
    1: "<17",
    2: "17–20",
    3: "17–20",
    4: "17–20",
    5: "17–20",
    6: "21–25",
    7: "21–25",
    8: "21–25",
    9: "21–25",
    10: "21–25",
    11: "26–40",
    12: "26–40",
    13: "26–40",
    14: ">40",
    15: ">40",
    16: ">40",
    17: ">40",
    18: ">40",
    19: ">40",
    20: ">40",
}

ORDEM_FAIXAS = [
    "<17",
    "17–20",
    "21–25",
    "26–40",
    ">40",
]

# ============================================================
# 2. ESTRUTURA HISTÓRICA DOS PERÍODOS
# ============================================================

# No desenho analítico do projeto:
# 1998–2008 → OBJETIVA
# 2009–2025 → CN, CH, LC, MT

def periodo_por_ano(ano):
    ano = int(ano)

    if 1998 <= ano <= 2008:
        return "1998_2008"

    if 2009 <= ano <= 2025:
        return "2009_2025"

    return None


def validar_colunas_desempenho(df_painel):

    faltantes = {}

    for periodo_id, disciplinas in ESPECIFICACOES_PERIODO.items():

        colunas = []

        for coluna_media, info in disciplinas.items():
            colunas.extend(
                [coluna_media, info["peso"]]
            )

        faltantes[periodo_id] = [
            coluna
            for coluna in colunas
            if coluna not in df_painel.columns
        ]

    return {
        periodo: colunas
        for periodo, colunas in faltantes.items()
        if colunas
    }

def periodos_analiticos():
    print("Períodos analíticos:")
    for periodo_id, periodo in PERIODOS.items():
        print(f" - {periodo['rotulo']}: "
              f"{periodo['estrutura']}")
    print()
    print(
            "✓ Estrutura histórica validada com as colunas "
            "OBJETIVA e ÁREAS.")


def cobertura_temporal(df_painel, df_grupo):
    anos_painel = sorted(df_painel["ano"].dropna().astype(int).unique())
    anos_grupo = sorted(df_grupo["ano"].dropna().astype(int).unique())

    ANO_FIM_GRUPOS_ANTIGO = min(
        PERIODO_ANTIGO["fim"],
        max([
            ano
            for ano in anos_grupo
            if PERIODO_ANTIGO["inicio"] <= ano <= PERIODO_ANTIGO["fim"]], default=PERIODO_ANTIGO["fim"]))

    ANO_FIM_GRUPOS_NOVO = min(
        PERIODO_ANTIGO["fim"],
        max([
            ano
            for ano in anos_grupo
            if PERIODO_NOVO["inicio"] <= ano <= PERIODO_NOVO["fim"]], default=PERIODO_NOVO["fim"]))

    print(f"Painel: {min(anos_painel)}–{max(anos_painel)}")
    print("Grupos — período antigo:",
          f"{PERIODO_ANTIGO['inicio']}–{ANO_FIM_GRUPOS_ANTIGO}")

    print("Grupos — período novo:",
          f"{PERIODO_NOVO['inicio']}–{ANO_FIM_GRUPOS_NOVO}"
          )
    print()
    print(
        "Obs.: análises por grupos utilizam somente os anos "
        "efetivamente presentes em desempenho_grupos_municipal.")
    return ANO_FIM_GRUPOS_ANTIGO,ANO_FIM_GRUPOS_NOVO


# ============================================================
# 4. VARIAÇÃO MUNICIPAL POR PERÍODO
# ============================================================

def calcular_variacao_municipal(painel,periodo,disciplina):
    inicio = periodo["inicio"]
    fim = periodo["fim"]

    base = painel[
        painel["ano"].isin([inicio, fim])
    ].copy()

    linhas = []

    for coluna, info in disciplina.items():

        inicio_df = (
            base[
                base["ano"] == inicio
            ][
                [
                    "CO_MUNICIPIO_TERRITORIO",
                    "NO_MUNICIPIO_TERRITORIO",
                    coluna,
                ]
            ]
            .rename(
                columns={
                    coluna: "media_inicial"
                }
            )
        )

        fim_df = (
            base[
                base["ano"] == fim
            ][
                [
                    "CO_MUNICIPIO_TERRITORIO",
                    coluna,
                ]
            ]
            .rename(
                columns={
                    coluna: "media_final"
                }
            )
        )

        temp = inicio_df.merge(
            fim_df,
            on="CO_MUNICIPIO_TERRITORIO",
            how="inner",
        )

        temp["delta"] = (
            temp["media_final"]
            - temp["media_inicial"]
        )

        temp["periodo"] = periodo["id"]
        temp["periodo_rotulo"] = periodo["rotulo"]
        temp["disciplina"] = info["nome"]
        temp["versao_redacao"] = (
            info.get("versao_redacao")
            if info.get("redacao")
            else None
        )

        linhas.append(temp)

    resultado = pd.concat(
        linhas,
        ignore_index=True,
    )

    return resultado[
        [
            "periodo",
            "periodo_rotulo",
            "disciplina",
            "versao_redacao",
            "CO_MUNICIPIO_TERRITORIO",
            "NO_MUNICIPIO_TERRITORIO",
            "media_inicial",
            "media_final",
            "delta",
        ]
    ]

# ============================================================
# 5. TENDÊNCIA MUNICIPAL POR PERÍODO
# ============================================================


def calcular_tendencias_municipais(
    painel,
    periodo,
    disciplinas,
    min_anos=5,
):

    dados_periodo = painel[
        painel["ano"].between(
            periodo["inicio"],
            periodo["fim"],
        )
    ].copy()

    resultados = []

    agrupado = dados_periodo.groupby(
        [
            "CO_MUNICIPIO_TERRITORIO",
            "NO_MUNICIPIO_TERRITORIO",
        ]
    )

    total_anos_periodo = (
        periodo["fim"]
        - periodo["inicio"]
        + 1
    )

    for (
        codigo,
        municipio
    ), dados_municipio in agrupado:

        for coluna, info in disciplinas.items():

            dados = (
                dados_municipio[
                    [
                        "ano",
                        coluna,
                    ]
                ]
                .dropna()
                .sort_values("ano")
            )

            if len(dados) < min_anos:
                continue

            regressao = linregress(
                dados["ano"],
                dados[coluna],
            )

            resultados.append({
                "periodo":
                    periodo["id"],

                "periodo_rotulo":
                    periodo["rotulo"],

                "disciplina":
                    info["nome"],

                "versao_redacao":
                    (
                        info.get("versao_redacao")
                        if info.get("redacao")
                        else None
                    ),

                "CO_MUNICIPIO_TERRITORIO":
                    codigo,

                "NO_MUNICIPIO_TERRITORIO":
                    municipio,

                "n_anos":
                    len(dados),

                "pct_cobertura":
                    len(dados)
                    / total_anos_periodo
                    * 100,

                "ano_inicial":
                    int(dados["ano"].min()),

                "ano_final":
                    int(dados["ano"].max()),

                "media_inicial":
                    float(
                        dados.loc[
                            dados["ano"].idxmin(),
                            coluna,
                        ]
                    ),

                "media_final":
                    float(
                        dados.loc[
                            dados["ano"].idxmax(),
                            coluna,
                        ]
                    ),

                "variacao_primeiro_ultimo":
                    float(
                        dados.loc[
                            dados["ano"].idxmax(),
                            coluna,
                        ]
                        - dados.loc[
                            dados["ano"].idxmin(),
                            coluna,
                        ]
                    ),

                "slope_pontos_ano":
                    float(regressao.slope),

                "erro_padrao_slope":
                    float(regressao.stderr),

                "r2":
                    float(regressao.rvalue ** 2),

                "p_valor":
                    float(regressao.pvalue),

                "direcao":
                    (
                        "positiva"
                        if regressao.slope > 0
                        else "negativa"
                        if regressao.slope < 0
                        else "nula"
                    ),
            })

    return pd.DataFrame(resultados)

def tend_val(tendencia_municipal_periodizada):
    MIN_ANOS_DISTRIBUICAO = 5

    tendencias_validas = (tendencia_municipal_periodizada[tendencia_municipal_periodizada["n_anos"]
                                                          >= MIN_ANOS_DISTRIBUICAO].copy())

    resumo_tendencias = (tendencias_validas.groupby(["periodo", "disciplina"])
                         .agg(
        n_municipios=(
            "CO_MUNICIPIO_TERRITORIO",
            "nunique",
        ),
        mediana_slope=(
            "slope_pontos_ano",
            "median",
        ),
        media_slope=(
            "slope_pontos_ano",
            "mean",
        ),
        pct_slope_positivo=(
            "slope_pontos_ano",
            lambda x: (x > 0).mean() * 100,
        ),
        n_tendencias_significativas=(
            "p_valor",
            lambda x: (x < 0.05).sum(),
        ),
        pct_tendencias_significativas=(
            "p_valor",
            lambda x: (x < 0.05).mean() * 100,
        ),
    ).reset_index())

    out= { 'tendencias_validas': tendencias_validas,
           'resumo_tendencias': resumo_tendencias}
    return out


# ============================================================
# 7. EVOLUÇÃO ESTADUAL POR PERÍODO
# ============================================================

def calcular_tendencia_estadual(painel,periodo,disciplinas):

    dados = painel[
        painel["ano"].between(
            periodo["inicio"],
            periodo["fim"],
        )
    ].copy()

    linhas_anuais = []

    for ano, grupo_ano in dados.groupby("ano"):

        linha = {
            "ano": int(ano),
            "periodo": periodo["id"],
            "periodo_rotulo": periodo["rotulo"],
        }

        for coluna, info in disciplinas.items():

            temp = grupo_ano[
                [
                    coluna,
                    info["peso"],
                ]
            ].dropna()

            temp = temp[
                temp[info["peso"]] > 0
            ]

            if temp.empty:
                linha[info["nome"]] = np.nan
            else:
                linha[info["nome"]] = (
                    (
                        temp[coluna]
                        * temp[info["peso"]]
                    ).sum()
                    / temp[info["peso"]].sum()
                )

        linhas_anuais.append(linha)

    serie = (
        pd.DataFrame(linhas_anuais)
        .sort_values("ano")
        .reset_index(drop=True)
    )

    resumo = []

    for coluna_logica, info in disciplinas.items():

        disciplina = info["nome"]

        dados_disciplina = (
            serie[
                [
                    "ano",
                    disciplina,
                ]
            ]
            .dropna()
            .sort_values("ano")
        )

        if len(dados_disciplina) < 3:
            continue

        regressao = linregress(
            dados_disciplina["ano"],
            dados_disciplina[disciplina],
        )

        resumo.append({
            "periodo":
                periodo["id"],

            "periodo_rotulo":
                periodo["rotulo"],

            "disciplina":
                disciplina,

            "versao_redacao":
                (
                    info.get("versao_redacao")
                    if info.get("redacao")
                    else None
                ),

            "n_anos":
                len(dados_disciplina),

            "media_inicial":
                float(
                    dados_disciplina.iloc[0][disciplina]
                ),

            "media_final":
                float(
                    dados_disciplina.iloc[-1][disciplina]
                ),

            "variacao_primeiro_ultimo":
                float(
                    dados_disciplina.iloc[-1][disciplina]
                    - dados_disciplina.iloc[0][disciplina]
                ),

            "slope_pontos_ano":
                float(regressao.slope),

            "erro_padrao_slope":
                float(regressao.stderr),

            "r2":
                float(regressao.rvalue ** 2),

            "p_valor":
                float(regressao.pvalue),
        })
    out={'dados':serie,
         'tendencia': pd.DataFrame(resumo)}
    return out
def plotar_tendencia_estadual(
    dados_serie,
    periodo,
    disciplinas,
):

    ordem = [
        info["nome"]
        for info in disciplinas.values()
    ]

    n = len(ordem)
    ncols = 2
    nrows = int(np.ceil(n / ncols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(14, 4.8 * nrows),
    )

    axes = np.atleast_1d(
        axes
    ).flatten()

    for i, disciplina in enumerate(ordem):

        dados_disciplina = (
            dados_serie[
                ["ano", disciplina]
            ]
            .dropna()
            .sort_values("ano")
        )

        x = dados_disciplina["ano"].values
        y = dados_disciplina[disciplina].values

        regressao = linregress(x, y)

        y_tendencia = (
            regressao.intercept
            + regressao.slope * x
        )

        sns.lineplot(
            x=x,
            y=y,
            marker="o",
            ax=axes[i],
            label="Média anual",
        )

        sns.lineplot(
            x=x,
            y=y_tendencia,
            linestyle="--",
            ax=axes[i],
            label=(
                f"Tendência "
                f"({regressao.slope:+.2f} ponto/ano)"
            ),
        )

        axes[i].set_title(
            disciplina
        )

        axes[i].set_xlabel("Ano")
        axes[i].set_ylabel("Média")

        axes[i].grid(
            axis="y",
            alpha=0.3,
        )

        axes[i].legend()

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        f"Evolução das médias e tendência — "
        f"{periodo['rotulo']}",
        fontsize=16,
        y=0.995,
    )

    plt.tight_layout(
        rect=[0, 0, 1, 0.98]
    )

    plt.show()


def rede_escolar(grupo):
    grupos_escola = (
        grupo[
            grupo["tipo_grupo"].astype("string").str.upper().eq("ESCOLA")]
        .copy())

    grupos_escola["periodo"] = (grupos_escola["ano"].apply(periodo_por_ano))

    grupos_escola["rede"] = pd.Series(pd.NA, index=grupos_escola.index, dtype="string")

    grupos_escola.loc[grupos_escola["grupo"].isin(["FEDERAL",
                                                   "ESTADUAL",
                                                   "MUNICIPAL"
                                                   ]), "rede"] = "PÚBLICA"
    grupos_escola.loc[grupos_escola["grupo"] == "PRIVADA", "rede"] = "PRIVADA"

    grupos_escola.loc[grupos_escola["grupo"] == "NAO_INFORMADA", "rede"] = "NAO_INFORMADA"

    grupos_escola = grupos_escola[grupos_escola["periodo"].notna()
                                  & grupos_escola["rede"].notna()].copy()

    grupos_escola["soma_ponderada"] = (grupos_escola["media"] * grupos_escola["n_validos"])

    rede_escolar_anual = (grupos_escola.groupby(
        ["periodo", "ano", "rede", "disciplina"], as_index=False).agg(
        soma_ponderada=("soma_ponderada", "sum",),
        n_validos=("n_validos", "sum",)))

    rede_escolar_anual["media"] = (rede_escolar_anual["soma_ponderada"] / rede_escolar_anual["n_validos"])

    rede_escolar_anual = (rede_escolar_anual[["periodo", "ano", "rede", "disciplina", "n_validos", "media"]]
                          .sort_values(["periodo", "ano", "disciplina", "rede"]).reset_index(drop=True))
    return rede_escolar_anual


def plotar_grupo_escola(dados,periodo_id,disciplinas):

    dados_periodo = dados[
        dados["periodo"] == periodo_id
    ].copy()

    ordem = [
        info["nome"]
        for info in disciplinas.values()
    ]

    n = len(ordem)
    ncols = 2
    nrows = int(np.ceil(n / ncols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(14, 4.5 * nrows),
    )

    axes = np.atleast_1d(
        axes
    ).flatten()

    for i, disciplina in enumerate(ordem):

        dados_disciplina = dados_periodo[
            dados_periodo["disciplina"] == disciplina
        ]

        sns.lineplot(
            data=dados_disciplina,
            x="ano",
            y="media",
            hue="rede",
            hue_order=[
                "PÚBLICA",
                "PRIVADA",
                "NAO_INFORMADA",
            ],
            marker="o",
            ax=axes[i],
        )

        axes[i].set_title(
            disciplina
        )

        axes[i].set_xlabel("Ano")
        axes[i].set_ylabel("Média")

        axes[i].grid(
            axis="y",
            alpha=0.3,
        )

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        "Evolução por rede escolar — "
        f"{PERIODOS[periodo_id]['rotulo']}",
        fontsize=16,
        y=0.995,
    )

    plt.tight_layout(
        rect=[0, 0, 1, 0.98])
    plt.show()


def sex_period(grupo):
    grupo_sexo = (grupo[
                      grupo["tipo_grupo"]
                  .astype("string")
                  .str.upper()
                  .eq("SEXO")
                  ]
                  .copy()
                  )

    grupo_sexo["periodo"] = (
        grupo_sexo["ano"]
        .apply(periodo_por_ano)
    )

    grupo_sexo["soma_ponderada"] = (
            grupo_sexo["media"]
            * grupo_sexo["n_validos"]
    )

    sexo_anual = (
        grupo_sexo
        .groupby(
            [
                "periodo",
                "ano",
                "grupo",
                "disciplina",
            ],
            as_index=False,
        )
        .agg(
            soma_ponderada=(
                "soma_ponderada",
                "sum",
            ),
            n_validos=(
                "n_validos",
                "sum",
            ),
        )
    )

    sexo_anual["media"] = (
            sexo_anual["soma_ponderada"]
            / sexo_anual["n_validos"]
    )

    sexo_anual = (
        sexo_anual[
            [
                "periodo",
                "ano",
                "grupo",
                "disciplina",
                "n_validos",
                "media",
            ]
        ]
        .sort_values(
            [
                "periodo",
                "ano",
                "disciplina",
                "grupo",
            ]
        )
        .reset_index(drop=True)
    )
    return sexo_anual

def plotar_grupo_sexo(dados,periodo_id,disciplinas):

    dados_periodo = dados[
        dados["periodo"] == periodo_id
    ].copy()

    ordem = [
        info["nome"]
        for info in disciplinas.values()
    ]

    n = len(ordem)
    ncols = 2
    nrows = int(np.ceil(n / ncols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(14, 4.5 * nrows),
    )

    axes = np.atleast_1d(
        axes
    ).flatten()

    for i, disciplina in enumerate(ordem):

        dados_disciplina = dados_periodo[
            dados_periodo["disciplina"] == disciplina
        ]

        sns.lineplot(
            data=dados_disciplina,
            x="ano",
            y="media",
            hue="grupo",
            marker="o",
            ax=axes[i],
        )

        axes[i].set_title(disciplina)
        axes[i].set_xlabel("Ano")
        axes[i].set_ylabel("Média")

        axes[i].grid(
            axis="y",
            alpha=0.3,
        )

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        "Evolução por sexo — "
        f"{PERIODOS[periodo_id]['rotulo']}",
        fontsize=16,
        y=0.995,
    )

    plt.tight_layout(
        rect=[0, 0, 1, 0.98]
    )

    plt.show()


def faixa_period(grupo):
    grupo_faixa = (
        grupo[
            grupo["tipo_grupo"]
            .astype("string")
            .str.upper()
            .eq("FAIXA_ETARIA")
        ]
            .copy()
    )

    grupo_faixa["periodo"] = (
        grupo_faixa["ano"]
        .apply(periodo_por_ano)
    )

    grupo_faixa["grupo_faixa"] = (
        pd.to_numeric(
            grupo_faixa["grupo"],
            errors="coerce",
        )
        .map(MAPA_FAIXA_5)
    )

    grupo_faixa = grupo_faixa[
        grupo_faixa["periodo"].notna()
        & grupo_faixa["grupo_faixa"].notna()
        ].copy()

    grupo_faixa["soma_ponderada"] = (
            grupo_faixa["media"]
            * grupo_faixa["n_validos"]
    )

    faixa_anual = (
        grupo_faixa
        .groupby(
            [
                "periodo",
                "ano",
                "grupo_faixa",
                "disciplina",
            ],
            as_index=False,
        )
        .agg(
            soma_ponderada=(
                "soma_ponderada",
                "sum",
            ),
            n_validos=(
                "n_validos",
                "sum",
            ),
        )
    )

    faixa_anual["media"] = (
            faixa_anual["soma_ponderada"]
            / faixa_anual["n_validos"]
    )

    faixa_anual = (
        faixa_anual[
            [
                "periodo",
                "ano",
                "grupo_faixa",
                "disciplina",
                "n_validos",
                "media",
            ]
        ]
        .sort_values(
            [
                "periodo",
                "ano",
                "disciplina",
                "grupo_faixa",
            ]
        )
        .reset_index(drop=True)
    )
    return faixa_anual

def plotar_grupo_faixa(dados,periodo_id,disciplinas):

    dados_periodo = dados[
        dados["periodo"] == periodo_id
    ].copy()

    ordem = [
        info["nome"]
        for info in disciplinas.values()
    ]

    n = len(ordem)
    ncols = 2
    nrows = int(np.ceil(n / ncols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(14, 4.5 * nrows),
    )

    axes = np.atleast_1d(
        axes
    ).flatten()

    for i, disciplina in enumerate(ordem):

        dados_disciplina = dados_periodo[
            dados_periodo["disciplina"] == disciplina
        ]

        sns.lineplot(
            data=dados_disciplina,
            x="ano",
            y="media",
            hue="grupo_faixa",
            hue_order=ORDEM_FAIXAS,
            marker="o",
            ax=axes[i],
        )

        axes[i].set_title(disciplina)
        axes[i].set_xlabel("Ano")
        axes[i].set_ylabel("Média")

        axes[i].grid(
            axis="y",
            alpha=0.3,
        )

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        "Evolução por faixa etária — "
        f"{PERIODOS[periodo_id]['rotulo']}",
        fontsize=16,
        y=0.995,
    )

    plt.tight_layout(
        rect=[0, 0, 1, 0.98]
    )

    plt.show()


def proporcao_period(faixa):
    faixa_participantes = faixa.copy()

    faixa_participantes["periodo"] = (
        faixa_participantes["ano"]
        .apply(periodo_por_ano)
    )

    faixa_participantes["grupo_faixa"] = (
        pd.to_numeric(
            faixa_participantes["TP_FAIXA_ETARIA"],
            errors="coerce",
        )
        .map(MAPA_FAIXA_5)
    )

    proporcao_faixa_periodizada = (
        faixa_participantes[
            faixa_participantes["periodo"].notna()
            & faixa_participantes["grupo_faixa"].notna()
            ]
        .groupby(
            [
                "periodo",
                "grupo_faixa",
            ],
            as_index=False,
        )["n_participantes"]
        .sum()
    )

    proporcao_faixa_periodizada["pct_participantes"] = (
        proporcao_faixa_periodizada
        .groupby("periodo")["n_participantes"]
        .transform(
            lambda x:
            x / x.sum() * 100
        )
    )

    proporcao_faixa_periodizada["grupo_faixa"] = pd.Categorical(
        proporcao_faixa_periodizada["grupo_faixa"],
        categories=ORDEM_FAIXAS,
        ordered=True,
    )

    proporcao_faixa_periodizada = (
        proporcao_faixa_periodizada
        .sort_values(
            [
                "periodo",
                "grupo_faixa",
            ]
        )
        .reset_index(drop=True)
    )
    return proporcao_faixa_periodizada

def calcular_estabilidade(painel,ano_inicial,ano_final,disciplinas,periodo_id):
    resultados = []

    for coluna, info in disciplinas.items():

        dados = (
            painel[
                painel["ano"].isin(
                    [ano_inicial, ano_final]
                )
            ][
                [
                    "CO_MUNICIPIO_TERRITORIO",
                    "NO_MUNICIPIO_TERRITORIO",
                    "ano",
                    coluna,
                ]
            ]
            .dropna(subset=[coluna])
            .pivot(
                index=[
                    "CO_MUNICIPIO_TERRITORIO",
                    "NO_MUNICIPIO_TERRITORIO",
                ],
                columns="ano",
                values=coluna,
            )
            .dropna()
        )

        if len(dados) < 3:
            continue

        if (
            ano_inicial not in dados.columns
            or ano_final not in dados.columns
        ):
            continue

        rho, p_valor = spearmanr(
            dados[ano_inicial],
            dados[ano_final],
        )

        resultados.append({
            "periodo": periodo_id,
            "ano_inicial": ano_inicial,
            "ano_final": ano_final,
            "disciplina": info["nome"],
            "versao_redacao": (
                info.get("versao_redacao")
                if info.get("redacao")
                else None
            ),
            "n_municipios": len(dados),
            "spearman": float(rho),
            "p_valor": float(p_valor),
        })

    return pd.DataFrame(resultados)
def construir_ranking_periodo(painel,periodo,disciplinas):
    resultados = []

    for ano in range(
        periodo["inicio"],
        periodo["fim"] + 1,
    ):

        dados_ano = painel[
            painel["ano"] == ano
        ].copy()

        for coluna_media, info in disciplinas.items():

            coluna_validos = info["peso"]

            dados = (
                dados_ano[
                    [
                        "CO_MUNICIPIO_TERRITORIO",
                        "NO_MUNICIPIO_TERRITORIO",
                        coluna_media,
                        coluna_validos,
                    ]
                ]
                .dropna(subset=[coluna_media])
                .copy()
            )

            top5 = (
                dados
                .sort_values(
                    [
                        coluna_media,
                        coluna_validos,
                        "NO_MUNICIPIO_TERRITORIO",
                    ],
                    ascending=[
                        False,
                        False,
                        True,
                    ],
                )
                .head(5)
                .copy()
            )

            bottom5 = (
                dados
                .sort_values(
                    [
                        coluna_media,
                        coluna_validos,
                        "NO_MUNICIPIO_TERRITORIO",
                    ],
                    ascending=[
                        True,
                        False,
                        True,
                    ],
                )
                .head(5)
                .copy()
            )

            for faixa_ranking, temp in [
                ("TOP 5", top5),
                ("BOTTOM 5", bottom5),
            ]:

                temp["posicao"] = range(
                    1,
                    len(temp) + 1,
                )

                temp["periodo"] = periodo["id"]
                temp["ano"] = ano
                temp["disciplina"] = info["nome"]
                temp["versao_redacao"] = (
                    info.get("versao_redacao")
                    if info.get("redacao")
                    else None
                )
                temp["faixa_ranking"] = faixa_ranking
                temp["media"] = temp[coluna_media]
                temp["n_validos"] = temp[coluna_validos]

                resultados.append(
                    temp[
                        [
                            "periodo",
                            "ano",
                            "disciplina",
                            "versao_redacao",
                            "faixa_ranking",
                            "posicao",
                            "CO_MUNICIPIO_TERRITORIO",
                            "NO_MUNICIPIO_TERRITORIO",
                            "media",
                            "n_validos",
                        ]
                    ]
                )

    return (
        pd.concat(
            resultados,
            ignore_index=True,
        )
        .sort_values(
            [
                "periodo",
                "ano",
                "disciplina",
                "faixa_ranking",
                "posicao",
            ]
        )
        .reset_index(drop=True)
    )

def freq_rank_period(ranking_anual_periodizado):
    frequencia_ranking_periodizada = (
        ranking_anual_periodizado
        .groupby(
            [
                "periodo",
                "disciplina",
                "faixa_ranking",
                "CO_MUNICIPIO_TERRITORIO",
                "NO_MUNICIPIO_TERRITORIO",
            ],
            as_index=False,
        )
        .agg(
            n_aparicoes=(
                "ano",
                "nunique",
            ),
            anos=(
                "ano",
                lambda x:
                ", ".join(
                    map(
                        str,
                        sorted(x),
                    )
                ),
            ),
        )
        .sort_values(
            [
                "periodo",
                "disciplina",
                "faixa_ranking",
                "n_aparicoes",
            ],
            ascending=[
                True,
                True,
                True,
                False,
            ],
        )
        .reset_index(drop=True)
    )

    recorrencia_top = (
        frequencia_ranking_periodizada[
            frequencia_ranking_periodizada["faixa_ranking"]
            == "TOP 5"
            ]
        .sort_values(
            [
                "periodo",
                "disciplina",
                "n_aparicoes",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
        .groupby(
            [
                "periodo",
                "disciplina",
            ],
            group_keys=False,
        )
        .head(5)
        .copy()
    )

    recorrencia_bottom = (
        frequencia_ranking_periodizada[
            frequencia_ranking_periodizada["faixa_ranking"]
            == "BOTTOM 5"
            ]
        .sort_values(
            [
                "periodo",
                "disciplina",
                "n_aparicoes",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
        .groupby(
            [
                "periodo",
                "disciplina",
            ],
            group_keys=False,
        )
        .head(5)
        .copy()
    )

    return frequencia_ranking_periodizada,recorrencia_top,recorrencia_bottom

def plotar_recorrencia(recorrencia,periodo_id,faixa_ranking):

    dados = recorrencia[
        recorrencia["periodo"] == periodo_id
    ].copy()

    if faixa_ranking == "TOP 5":
        dados = (
            dados
            .sort_values(
                "n_aparicoes",
                ascending=False,
            )
        )
    else:
        dados = (
            dados
            .sort_values(
                "n_aparicoes",
                ascending=True,
            )
        )

    ordem = (
        dados["disciplina"]
        .drop_duplicates()
        .tolist()
    )

    n = len(ordem)
    ncols = 2
    nrows = int(np.ceil(n / ncols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(15, 4.5 * nrows),
    )

    axes = np.atleast_1d(
        axes
    ).flatten()

    for i, disciplina in enumerate(ordem):

        temp = dados[
            dados["disciplina"] == disciplina
        ].copy()

        sns.barplot(
            data=temp,
            x="n_aparicoes",
            y="NO_MUNICIPIO_TERRITORIO",
            ax=axes[i],
        )

        axes[i].set_title(
            f"{disciplina} — {faixa_ranking}"
        )

        axes[i].set_xlabel("Número de aparições")
        axes[i].set_ylabel("Município")

        axes[i].grid(
            axis="x",
            alpha=0.3,
        )

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        f"Recorrência nos extremos — "
        f"{PERIODOS[periodo_id]['rotulo']} — "
        f"{faixa_ranking}",
        fontsize=16,
        y=0.995,
    )

    plt.tight_layout(
        rect=[0, 0, 1, 0.98]
    )

    plt.show()

def gap_period(grupo):
    grupos_gap = (
        grupo[
            grupo["tipo_grupo"]
            .astype("string")
            .str.upper()
            .eq("ESCOLA")
        ]
            .copy()
    )

    grupos_gap["periodo"] = (
        grupos_gap["ano"]
        .apply(periodo_por_ano)
    )

    grupos_gap["rede"] = pd.Series(
        pd.NA,
        index=grupos_gap.index,
        dtype="string",
    )

    grupos_gap.loc[
        grupos_gap["grupo"].isin(
            [
                "FEDERAL",
                "ESTADUAL",
                "MUNICIPAL",
            ]
        ),
        "rede",
    ] = "PÚBLICA"

    grupos_gap.loc[
        grupos_gap["grupo"] == "PRIVADA",
        "rede",
    ] = "PRIVADA"

    grupos_gap.loc[
        grupos_gap["grupo"] == "NAO_INFORMADA",
        "rede",
    ] = "NAO_INFORMADA"

    grupos_gap = grupos_gap[
        grupos_gap["periodo"].notna()
        & grupos_gap["rede"].notna()
        ].copy()

    grupos_gap["soma_ponderada"] = (
            grupos_gap["media"]
            * grupos_gap["n_validos"]
    )

    rede_gap = (
        grupos_gap
        .groupby(
            [
                "periodo",
                "ano",
                "rede",
                "disciplina",
            ],
            as_index=False,
        )
        .agg(
            soma_ponderada=(
                "soma_ponderada",
                "sum",
            ),
            n_validos=(
                "n_validos",
                "sum",
            ),
        )
    )

    rede_gap["media"] = (
            rede_gap["soma_ponderada"]
            / rede_gap["n_validos"]
    )

    medias_rede = (
        rede_gap
        .pivot(
            index=[
                "periodo",
                "ano",
                "disciplina",
            ],
            columns="rede",
            values="media",
        )
        .reset_index()
        .rename(
            columns={
                "PÚBLICA": "media_publica",
                "PRIVADA": "media_privada",
            }
        )
    )

    validos_rede = (
        rede_gap
        .pivot(
            index=[
                "periodo",
                "ano",
                "disciplina",
            ],
            columns="rede",
            values="n_validos",
        )
        .reset_index()
        .rename(
            columns={
                "PÚBLICA": "n_validos_publica",
                "PRIVADA": "n_validos_privada",
            }
        )
    )

    nao_informada = (
        rede_gap[
            rede_gap["rede"] == "NAO_INFORMADA"
            ]
        [
            [
                "periodo",
                "ano",
                "disciplina",
                "n_validos",
            ]
        ]
        .rename(
            columns={
                "n_validos": "n_nao_informada"
            }
        )
    )

    resultado_gap_periodizado = (
        medias_rede
        .merge(
            validos_rede,
            on=[
                "periodo",
                "ano",
                "disciplina",
            ],
            how="left",
        )
        .merge(
            nao_informada,
            on=[
                "periodo",
                "ano",
                "disciplina",
            ],
            how="left",
        )
    )

    resultado_gap_periodizado[
        "n_nao_informada"
    ] = (
        resultado_gap_periodizado[
            "n_nao_informada"
        ]
        .fillna(0)
    )

    resultado_gap_periodizado[
        "gap_privada_publica"
    ] = (
            resultado_gap_periodizado["media_privada"]
            - resultado_gap_periodizado["media_publica"]
    )
    return  resultado_gap_periodizado

def plotar_gap_rede(dados,periodo_id):

    temp = dados[
        dados["periodo"] == periodo_id
    ].copy()

    disciplinas = (
        temp["disciplina"]
        .drop_duplicates()
        .tolist()
    )

    n = len(disciplinas)
    ncols = 2
    nrows = int(np.ceil(n / ncols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(14, 4.5 * nrows),
    )

    axes = np.atleast_1d(
        axes
    ).flatten()

    for i, disciplina in enumerate(
        disciplinas
    ):

        serie = temp[
            temp["disciplina"] == disciplina
        ]

        sns.lineplot(
            data=serie,
            x="ano",
            y="gap_privada_publica",
            marker="o",
            ax=axes[i],
        )

        axes[i].axhline(
            0,
            linestyle="--",
            linewidth=1,
        )

        axes[i].set_title(disciplina)
        axes[i].set_xlabel("Ano")
        axes[i].set_ylabel(
            "Privada − Pública"
        )

        axes[i].grid(
            axis="y",
            alpha=0.3,
        )

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        "Diferença de desempenho — "
        f"{PERIODOS[periodo_id]['rotulo']}",
        fontsize=16,
        y=0.995,
    )

    plt.tight_layout(
        rect=[0, 0, 1, 0.98]
    )

    plt.show()


if __name__ == "__main__":
    periodos_analiticos()

# ============================================================
# CONFIGURAÇÃO DA ANÁLISE TRANSVERSAL POR ANO
# ============================================================

def configuracao_analise_transversal(ano):
    """Retorna a estrutura de desempenho válida para um ano do ENEM.

    1998–2008: OBJETIVA + REDAÇÃO (versão antiga).
    2009–2025: CN, CH, LC, MT + REDAÇÃO (versão nova).

    Evita misturar disciplinas/estruturas de avaliação incompatíveis.
    """
    periodo_id = periodo_por_ano(ano)
    if periodo_id is None:
        raise ValueError(
            f"Ano {ano} fora do intervalo analítico 1998–2025."
        )

    periodo = PERIODOS[periodo_id]
    disciplinas = ESPECIFICACOES_PERIODO[periodo_id]

    return {
        "ano": int(ano),
        "periodo_id": periodo_id,
        "periodo": periodo,
        "disciplinas": disciplinas,
        "colunas_medias": list(disciplinas.keys()),
        "nomes_disciplinas": {
            coluna: info["nome"]
            for coluna, info in disciplinas.items()
        },
        "ordem_disciplinas": [
            info["nome"] for info in disciplinas.values()
        ],
    }

