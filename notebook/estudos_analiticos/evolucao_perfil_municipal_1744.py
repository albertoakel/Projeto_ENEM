"""
Funções para analisar a evolução do desempenho municipal no ENEM
e, complementarmente, acompanhar perfis relativos obtidos por K-Means.

Integração prevista com o Projeto ENEM:
    desempenho_municipal = eda2.preparar_desempenho_territorial_dsp(
        dsp,
        referencia=TIPO_REFERENCIA,
        n_minimo_participantes=N_MINIMO_PARTICIPANTES,
        anos_inicio_comparavel=2002,
        painel=painel,
    )

    from src.utils.evolucao_perfil_municipal import (
        preparar_painel_municipal,
        resumir_evolucao_anual,
        calcular_evolucao_municipal,
        ajustar_clusters_por_ano,
        resumir_transicoes_clusters,
    )

Observação metodológica:
- A evolução das notas é calculada nas unidades originais (pontos ENEM).
- O K-Means é ajustado separadamente em cada ano, após padronização daquele ano.
- Os rótulos dos clusters são ordenados pela média geral do próprio ano:
  Perfil A = menor média relativa; Perfil B = maior média relativa.
- Portanto, o rótulo do cluster descreve uma posição relativa anual, não
  uma escala absoluta nem uma trajetória de melhora/piora.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


DISCIPLINAS_ENEM_2009 = ("CH", "CN", "LC", "MT", "REDACAO")

COLUNAS_CHAVE = (
    "ano",
    "CO_MUNICIPIO_TERRITORIO",
    "NO_MUNICIPIO_TERRITORIO",
    "disciplina",
    "media_ponderada",
)


def _validar_colunas(
    df: pd.DataFrame,
    colunas: Iterable[str],
    nome_df: str = "DataFrame",
) -> None:
    """Gera erro explícito quando faltam colunas necessárias."""
    faltantes = sorted(set(colunas).difference(df.columns))
    if faltantes:
        raise ValueError(f"{nome_df}: colunas ausentes: {faltantes}")


def preparar_painel_municipal(
    desempenho_municipal: pd.DataFrame,
    anos: Iterable[int] = range(2009, 2024),
    disciplinas: Sequence[str] = DISCIPLINAS_ENEM_2009,
    exigir_elegibilidade: bool = True,
) -> pd.DataFrame:
    """
    Converte a base longa município × disciplina em painel município × ano.

    A entrada deve ser o DataFrame retornado por
    eda2.preparar_desempenho_territorial_dsp(), isto é, a mesma preparação
    já utilizada no Q5/Q8.

    Retorna uma linha por município/ano, com uma coluna para cada disciplina,
    número de participantes e média simples das cinco disciplinas.

    A função não recalcula médias a partir dos microdados.
    """
    _validar_colunas(desempenho_municipal, COLUNAS_CHAVE, "desempenho_municipal")

    anos = sorted({int(ano) for ano in anos})
    disciplinas = list(disciplinas)

    base = desempenho_municipal.copy()
    base["ano"] = pd.to_numeric(base["ano"], errors="coerce")
    base["media_ponderada"] = pd.to_numeric(
        base["media_ponderada"], errors="coerce"
    )

    base = base.loc[
        base["ano"].isin(anos) & base["disciplina"].isin(disciplinas)
    ].copy()

    if exigir_elegibilidade:
        if "elegivel_analise_principal" not in base.columns:
            raise ValueError(
                "A coluna 'elegivel_analise_principal' não existe. "
                "Use a saída da preparação territorial do Q5/Q8 ou "
                "defina exigir_elegibilidade=False conscientemente."
            )
        base = base.loc[base["elegivel_analise_principal"].fillna(False)].copy()

    chave = ["ano", "CO_MUNICIPIO_TERRITORIO", "disciplina"]
    duplicados = int(base.duplicated(chave).sum())
    if duplicados:
        raise ValueError(
            f"Foram encontradas {duplicados} duplicidades em ano × município "
            "× disciplina. Verifique a preparação de desempenho municipal."
        )

    indice = ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO"]
    notas = (
        base.pivot(
            index=indice,
            columns="disciplina",
            values="media_ponderada",
        )
        .reindex(columns=disciplinas)
        .reset_index()
    )
    notas.columns.name = None

    if "n_participantes" in base.columns:
        participantes = (
            base.groupby(indice, dropna=False)["n_participantes"]
            .max()
            .rename("n_participantes")
            .reset_index()
        )
        notas = notas.merge(participantes, on=indice, how="left", validate="one_to_one")
    else:
        notas["n_participantes"] = np.nan

    # A média geral só é calculada quando todas as disciplinas solicitadas
    # estão disponíveis para aquele município/ano.
    notas["n_disciplinas_validas"] = notas[disciplinas].notna().sum(axis=1)
    notas["media_geral_5_disciplinas"] = notas[disciplinas].mean(
        axis=1, skipna=False
    )

    return notas.sort_values(
        ["ano", "CO_MUNICIPIO_TERRITORIO"]
    ).reset_index(drop=True)


def resumir_evolucao_anual(
    painel_municipal: pd.DataFrame,
    disciplinas: Sequence[str] = DISCIPLINAS_ENEM_2009,
) -> pd.DataFrame:
    """
    Resume o desempenho em cada edição, preservando a unidade de análise.

    Produz:
    - média e mediana das médias municipais (municípios têm peso igual);
    - média ponderada pelo número de participantes, quando disponível;
    - número de municípios e total de participantes.

    A média municipal não deve ser confundida com a média individual de todos
    os participantes. As duas medidas são apresentadas separadamente.
    """
    disciplinas = list(disciplinas)
    _validar_colunas(
        painel_municipal,
        ["ano", "CO_MUNICIPIO_TERRITORIO", "n_participantes", *disciplinas],
        "painel_municipal",
    )

    linhas = []
    for ano, grupo in painel_municipal.groupby("ano", sort=True):
        registro = {
            "ano": int(ano),
            "n_municipios": grupo["CO_MUNICIPIO_TERRITORIO"].nunique(),
            "participantes_total": pd.to_numeric(
                grupo["n_participantes"], errors="coerce"
            ).sum(min_count=1),
        }

        pesos = pd.to_numeric(grupo["n_participantes"], errors="coerce")
        for disciplina in disciplinas:
            valores = pd.to_numeric(grupo[disciplina], errors="coerce")
            validos = valores.notna()
            registro[f"media_municipal_{disciplina}"] = valores.mean()
            registro[f"mediana_municipal_{disciplina}"] = valores.median()

            peso_valido = validos & pesos.notna() & pesos.gt(0)
            if peso_valido.any():
                registro[f"media_ponderada_participantes_{disciplina}"] = np.average(
                    valores.loc[peso_valido], weights=pesos.loc[peso_valido]
                )
            else:
                registro[f"media_ponderada_participantes_{disciplina}"] = np.nan

        valores_gerais = grupo["media_geral_5_disciplinas"]
        registro["media_municipal_geral"] = valores_gerais.mean()
        registro["mediana_municipal_geral"] = valores_gerais.median()

        linhas.append(registro)

    return pd.DataFrame(linhas).sort_values("ano").reset_index(drop=True)


def calcular_evolucao_municipal(
    painel_municipal: pd.DataFrame,
    ano_inicial: int = 2009,
    ano_final: int = 2023,
    disciplinas: Sequence[str] = DISCIPLINAS_ENEM_2009,
    somente_painel_completo: bool = False,
) -> pd.DataFrame:
    """
    Calcula a variação real das notas municipais entre dois anos.

    Delta = nota no ano final - nota no ano inicial.
    Valores positivos indicam aumento da nota; negativos, redução.

    Por padrão, mantém municípios com dados nos dois anos. Com
    somente_painel_completo=True, exige também todas as disciplinas nos
    dois anos.
    """
    disciplinas = list(disciplinas)
    _validar_colunas(
        painel_municipal,
        ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO",
         "media_geral_5_disciplinas", *disciplinas],
        "painel_municipal",
    )

    base = painel_municipal.loc[
        painel_municipal["ano"].isin([ano_inicial, ano_final])
    ].copy()

    if base.duplicated(["ano", "CO_MUNICIPIO_TERRITORIO"]).any():
        raise ValueError("O painel possui mais de uma linha por município/ano.")

    colunas_valor = ["media_geral_5_disciplinas", *disciplinas]
    wide = base.pivot(
        index="CO_MUNICIPIO_TERRITORIO",
        columns="ano",
        values=colunas_valor,
    )

    anos_presentes = set(wide.columns.get_level_values(1))
    if not {ano_inicial, ano_final}.issubset(anos_presentes):
        raise ValueError("Não há dados para um dos anos informados.")

    nomes = (
        base.sort_values("ano")
        .drop_duplicates("CO_MUNICIPIO_TERRITORIO", keep="last")
        .set_index("CO_MUNICIPIO_TERRITORIO")["NO_MUNICIPIO_TERRITORIO"]
    )
    resultado = pd.DataFrame(index=wide.index)
    resultado.index.name = "CO_MUNICIPIO_TERRITORIO"
    resultado["NO_MUNICIPIO_TERRITORIO"] = nomes

    for coluna in colunas_valor:
        inicial = wide[(coluna, ano_inicial)] if (coluna, ano_inicial) in wide else np.nan
        final = wide[(coluna, ano_final)] if (coluna, ano_final) in wide else np.nan
        resultado[f"{coluna}_{ano_inicial}"] = inicial
        resultado[f"{coluna}_{ano_final}"] = final
        resultado[f"delta_{coluna}"] = resultado[f"{coluna}_{ano_final}"] - resultado[
            f"{coluna}_{ano_inicial}"
        ]

    resultado = resultado.reset_index()
    if somente_painel_completo:
        colunas_exigir = [
            f"{coluna}_{ano_inicial}" for coluna in colunas_valor
        ] + [f"{coluna}_{ano_final}" for coluna in colunas_valor]
        resultado = resultado.dropna(subset=colunas_exigir)

    return resultado.sort_values(
        "delta_media_geral_5_disciplinas", ascending=False
    ).reset_index(drop=True)


def ajustar_clusters_por_ano(
    painel_municipal: pd.DataFrame,
    anos: Iterable[int] = range(2009, 2024),
    disciplinas: Sequence[str] = DISCIPLINAS_ENEM_2009,
    k: int = 2,
    random_state: int = 42,
    n_init: int = 50,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ajusta K-Means separadamente em cada ano e ordena os perfis pela média.

    Retorna:
    1. classificação município/ano com cluster_original e perfil_relativo;
    2. diagnóstico anual com municípios, silhouette e médias dos perfis.

    IMPORTANTE: o K-Means é recalculado em cada edição. Perfil A/B representa
    a posição relativa dentro daquele ano. A evolução absoluta das notas
    deve ser analisada pelas funções de desempenho, não pelo rótulo do cluster.
    """
    disciplinas = list(disciplinas)
    _validar_colunas(
        painel_municipal,
        ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO",
         "media_geral_5_disciplinas", *disciplinas],
        "painel_municipal",
    )

    classificacoes = []
    diagnosticos = []

    for ano in sorted({int(a) for a in anos}):
        grupo = painel_municipal.loc[
            painel_municipal["ano"].eq(ano)
        ].dropna(subset=disciplinas).copy()

        # K-Means precisa de pelo menos k municípios e dados não constantes.
        if len(grupo) <= k:
            diagnosticos.append({
                "ano": ano,
                "n_municipios": len(grupo),
                "k": k,
                "silhouette": np.nan,
                "status": "municípios insuficientes",
            })
            continue

        X = grupo[disciplinas].astype(float)
        variaveis = X.columns[X.var() > 0].tolist()
        if len(variaveis) < 2:
            diagnosticos.append({
                "ano": ano,
                "n_municipios": len(grupo),
                "k": k,
                "silhouette": np.nan,
                "status": "variabilidade insuficiente",
            })
            continue

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X[variaveis])

        modelo = KMeans(
            n_clusters=k,
            random_state=random_state,
            n_init=n_init,
        )
        rotulos = modelo.fit_predict(X_scaled)

        if len(np.unique(rotulos)) < 2:
            sil = np.nan
        else:
            sil = silhouette_score(X_scaled, rotulos)

        grupo["cluster_original"] = rotulos
        medias = grupo.groupby("cluster_original")[
            "media_geral_5_disciplinas"
        ].mean().sort_values()

        ordem = medias.index.tolist()
        nomes_perfil = {
            cluster: f"Perfil {chr(65 + pos)}" for pos, cluster in enumerate(ordem)
        }
        grupo["perfil_relativo"] = grupo["cluster_original"].map(nomes_perfil)
        grupo["ano"] = ano
        classificacoes.append(
            grupo[
                [
                    "ano",
                    "CO_MUNICIPIO_TERRITORIO",
                    "NO_MUNICIPIO_TERRITORIO",
                    "cluster_original",
                    "perfil_relativo",
                    "media_geral_5_disciplinas",
                    *disciplinas,
                ]
            ]
        )

        for cluster, media in medias.items():
            sub = grupo.loc[grupo["cluster_original"].eq(cluster)]
            diagnosticos.append({
                "ano": ano,
                "n_municipios": len(grupo),
                "k": k,
                "silhouette": sil,
                "cluster_original": int(cluster),
                "perfil_relativo": nomes_perfil[cluster],
                "n_municipios_cluster": sub["CO_MUNICIPIO_TERRITORIO"].nunique(),
                "media_geral_cluster": media,
                "status": "ok",
            })

    classificacao = (
        pd.concat(classificacoes, ignore_index=True)
        if classificacoes else pd.DataFrame()
    )
    diagnostico = pd.DataFrame(diagnosticos)
    return classificacao, diagnostico


def resumir_transicoes_clusters(
    classificacao: pd.DataFrame,
    ano_inicial: int,
    ano_final: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Resume mudanças de perfil relativo entre dois anos.

    É uma análise de mudança de posição relativa, não de evolução absoluta
    das notas. Para evolução das notas, use calcular_evolucao_municipal().
    """
    _validar_colunas(
        classificacao,
        ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO",
         "perfil_relativo"],
        "classificacao",
    )

    base = classificacao.loc[
        classificacao["ano"].isin([ano_inicial, ano_final])
    ].copy()

    wide = base.pivot(
        index="CO_MUNICIPIO_TERRITORIO",
        columns="ano",
        values="perfil_relativo",
    )
    wide = wide.dropna(subset=[ano_inicial, ano_final]).reset_index()
    wide = wide.rename(columns={
        ano_inicial: f"perfil_{ano_inicial}",
        ano_final: f"perfil_{ano_final}",
    })

    nomes = (
        base.drop_duplicates("CO_MUNICIPIO_TERRITORIO")
        .set_index("CO_MUNICIPIO_TERRITORIO")["NO_MUNICIPIO_TERRITORIO"]
    )
    wide.insert(
        1,
        "NO_MUNICIPIO_TERRITORIO",
        wide["CO_MUNICIPIO_TERRITORIO"].map(nomes),
    )
    matriz = pd.crosstab(
        wide[f"perfil_{ano_inicial}"],
        wide[f"perfil_{ano_final}"],
        margins=False,
    )
    return wide, matriz


def calcular_tendencia_municipal(
    painel_municipal: pd.DataFrame,
    disciplinas: Sequence[str] = DISCIPLINAS_ENEM_2009,
    ano_inicio: int = 2009,
    ano_fim: int = 2023,
    minimo_edicoes: int = 5,
) -> pd.DataFrame:
    """
    Estima a tendência linear das notas de cada município e disciplina.

    A inclinação é expressa em pontos ENEM por ano:
    - inclinação positiva: tendência de aumento;
    - inclinação negativa: tendência de redução;
    - próxima de zero: pouca tendência linear no período.

    Também retorna a diferença observada entre a primeira e a última edição
    disponível para aquele município/disciplina dentro do intervalo.

    A inclinação resume a trajetória e não implica que a evolução tenha sido
    linear em todos os anos. Municípios com menos de minimo_edicoes são
    excluídos do resultado.
    """
    disciplinas = list(disciplinas)
    _validar_colunas(
        painel_municipal,
        ["ano", "CO_MUNICIPIO_TERRITORIO", "NO_MUNICIPIO_TERRITORIO",
         *disciplinas],
        "painel_municipal",
    )

    base = painel_municipal.loc[
        painel_municipal["ano"].between(ano_inicio, ano_fim)
    ].copy()

    if base.duplicated(["ano", "CO_MUNICIPIO_TERRITORIO"]).any():
        raise ValueError("O painel possui mais de uma linha por município/ano.")

    saidas = []
    for codigo, grupo in base.groupby("CO_MUNICIPIO_TERRITORIO", sort=False):
        nome = grupo["NO_MUNICIPIO_TERRITORIO"].dropna()
        nome = nome.iloc[0] if not nome.empty else None

        for disciplina in disciplinas:
            serie = grupo[["ano", disciplina]].dropna().copy()
            serie[disciplina] = pd.to_numeric(serie[disciplina], errors="coerce")
            serie = serie.dropna().sort_values("ano")

            if len(serie) < minimo_edicoes:
                continue

            x = serie["ano"].to_numpy(dtype=float)
            y = serie[disciplina].to_numpy(dtype=float)
            inclinacao, intercepto = np.polyfit(x, y, deg=1)

            saidas.append({
                "CO_MUNICIPIO_TERRITORIO": codigo,
                "NO_MUNICIPIO_TERRITORIO": nome,
                "disciplina": disciplina,
                "ano_primeiro_dado": int(x.min()),
                "ano_ultimo_dado": int(x.max()),
                "n_edicoes": len(serie),
                "nota_primeira_edicao": float(y[0]),
                "nota_ultima_edicao": float(y[-1]),
                "delta_primeira_ultima": float(y[-1] - y[0]),
                "tendencia_pontos_por_ano": float(inclinacao),
                "direcao_tendencia": (
                    "aumento" if inclinacao > 0
                    else "redução" if inclinacao < 0
                    else "estável"
                ),
            })

    return pd.DataFrame(saidas).sort_values(
        ["disciplina", "tendencia_pontos_por_ano"],
        ascending=[True, False],
    ).reset_index(drop=True)
