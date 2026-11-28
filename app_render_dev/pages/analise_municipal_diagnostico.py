"""Instrumentação temporária do callback da página Análise.

Preserva os cálculos da implementação original em pages.analise_municipal e
acrescenta snapshots de RSS/USS e tamanho profundo dos DataFrames entre etapas.
"""

import sys
import time
from functools import wraps

import numpy as np
import pandas as pd
import psutil
from dash import Input, Output, State, html, no_update

from dash_utils.perf import LOG, etapa, medir_callback
from pages import analise_municipal as base

_PROCESSO = psutil.Process()
_MB = 1024 ** 2

# Expõe o layout original sem modificações.
criar_layout_analise = base.criar_layout_analise


def _snapshot():
    info = _PROCESSO.memory_full_info()
    return info.rss / _MB, getattr(info, "uss", 0) / _MB


def _df_resumo(df):
    if not isinstance(df, pd.DataFrame):
        return None
    try:
        deep = float(df.memory_usage(index=True, deep=True).sum() / _MB)
    except Exception:
        deep = float("nan")
    return f"shape={df.shape} | deep={deep:.2f} MB"


def _fig_resumo(fig):
    if not hasattr(fig, "data"):
        return None
    n_traces = len(fig.data)
    n_points = 0
    for trace in fig.data:
        for attr in ("x", "y", "z"):
            valores = getattr(trace, attr, None)
            if valores is not None:
                try:
                    n_points += len(valores)
                except TypeError:
                    pass
    return f"traces={n_traces} | pontos_xy_z={n_points}"


def _obj_resumo(obj):
    if isinstance(obj, pd.DataFrame):
        return _df_resumo(obj)
    if isinstance(obj, tuple):
        partes = [_obj_resumo(x) for x in obj]
        partes = [x for x in partes if x]
        return " ; ".join(partes) if partes else f"tuple_len={len(obj)}"
    return _fig_resumo(obj)


def _marcar(etapa_nome, **objetos):
    rss, uss = _snapshot()
    detalhes = []
    for nome, obj in objetos.items():
        resumo = _obj_resumo(obj)
        if resumo:
            detalhes.append(f"{nome}[{resumo}]")
    sufixo = " | " + " || ".join(detalhes) if detalhes else ""
    LOG.info("DIAG ANALISE | %-38s | RSS=%.1f MB | USS=%.1f MB%s",
             etapa_nome, rss, uss, sufixo)
    return rss, uss


def _executar(etapa_nome, func, *args, **kwargs):
    rss_ini, uss_ini = _snapshot()
    inicio = time.perf_counter()
    try:
        resultado = func(*args, **kwargs)
    except Exception:
        rss_fim, uss_fim = _snapshot()
        LOG.exception(
            "DIAG ANALISE FALHA | %s | RSS=%+.1f MB | USS=%+.1f MB",
            etapa_nome, rss_fim - rss_ini, uss_fim - uss_ini,
        )
        raise
    rss_fim, uss_fim = _snapshot()
    resumo = _obj_resumo(resultado)
    extra = f" | resultado={resumo}" if resumo else ""
    LOG.info(
        "DIAG ANALISE ETAPA | %-32s | RSS=%+.1f MB | USS=%+.1f MB | "
        "tempo=%.3f s%s",
        etapa_nome, rss_fim - rss_ini, uss_fim - uss_ini,
        time.perf_counter() - inicio, extra,
    )
    return resultado


def registrar_callbacks_analise(app, carregar_dados):
    """Registra os mesmos callbacks, com checkpoints internos de memória."""

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
        opcoes_df = base._painel_municipios(dados["painel"])
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
    @medir_callback("análise · atualizar_analise (diagnóstico por etapa)")
    def atualizar_analise(
        referencia, principal, comparacao, dependencia,
        disciplina, ano, uf, pathname
    ):
        if pathname not in ("/analise-municipal", "/analise") or not principal:
            return (no_update,) * 7

        _marcar(
            "início callback",
            statsmodels_carregado=("statsmodels.api" in sys.modules),
        )

        dados = _executar("carregar_dados", carregar_dados, uf, referencia=referencia)
        _marcar("dados recebidos", painel=dados["painel"], grupo=dados["grupo"])

        painel = _executar("painel.copy(deep=True)", dados["painel"].copy)
        _marcar("após cópia painel", painel=painel)
        grupo = _executar("grupo.copy(deep=True)", dados["grupo"].copy)
        _marcar("após cópia grupo", grupo=grupo)

        nomes = _executar("_nomes_municipios", base._nomes_municipios, painel)
        _marcar("após nomes municipais")
        codigos = [principal] + [c for c in (comparacao or []) if c != principal][:4]
        nomes_selecionados = {c: nomes.get(c, c) for c in codigos}

        def preparar_painel():
            painel["codigo"] = base._codigo(painel["CO_MUNICIPIO_TERRITORIO"])
            painel["ano"] = pd.to_numeric(painel["ano"], errors="coerce")
            return painel[
                (painel["codigo"] == principal)
                & (painel["ano"] == int(ano))
            ]

        atual = _executar("normalizar painel + selecionar ano", preparar_painel)
        _marcar("painel preparado", painel=painel, atual=atual)

        with etapa("análise: série de participantes"):
            serie_part = _executar(
                "_serie_participantes",
                base._serie_participantes, painel, codigos, dependencia,
            )
        _marcar("após série participantes", serie_part=serie_part)

        with etapa("análise: série de desempenho"):
            serie_disc = _executar(
                "_serie_desempenho",
                base._serie_desempenho, grupo, codigos, dependencia,
                base.DISCIPLINAS[disciplina],
            )
        _marcar("após série desempenho", serie_disc=serie_disc)

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
        total = total_ano["participantes"].sum() if not total_ano.empty else np.nan
        ano_atual = int(ano)
        ano_anterior = ano_atual - 1
        participantes_atual = serie_part_principal.loc[
            serie_part_principal["ano"] == ano_atual, "participantes"
        ].sum()
        dados_anterior = serie_part_principal.loc[
            serie_part_principal["ano"] == ano_anterior, "participantes"
        ]
        participantes_anterior = (
            dados_anterior.sum() if not dados_anterior.empty else np.nan
        )
        variacao = (
            (participantes_atual / participantes_anterior - 1) * 100
            if pd.notna(participantes_anterior) and participantes_anterior > 0
            else np.nan
        )
        kpis = _executar(
            "construção dos KPIs",
            lambda: [
                base._card("Participantes no ano", total, f"Ano {ano}"),
                base._card("Variação anual de participantes", variacao,
                           "Em relação ao ano anterior (%)"),
                base._card("Anos com dados", int(serie_part_principal["ano"].nunique()),
                           "Série de participação"),
                base._card(f"Média — {disciplina}", media,
                           f"N válido: {n_validos:,}".replace(",", ".")),
            ],
        )
        _marcar("após KPIs")

        fig_part = _executar(
            "figura evolução participantes",
            base._figura_evolucao_participantes,
            painel, codigos, dependencia, nomes_selecionados,
            serie=serie_part,
        )
        _marcar("após figura participantes", figura=fig_part)

        statsmodels_antes = "statsmodels.api" in sys.modules
        fig_desempenho, resumo_tendencia_redacao = _executar(
            "figura desempenho + tendências",
            base._figura_evolucao_desempenho,
            grupo, codigos, dependencia, disciplina, nomes_selecionados,
            serie=serie_disc,
        )
        statsmodels_depois = "statsmodels.api" in sys.modules
        LOG.info(
            "DIAG ANALISE STATSMODELS | antes=%s | depois=%s",
            statsmodels_antes, statsmodels_depois,
        )
        _marcar("após figura desempenho", figura=fig_desempenho)

        with etapa("análise: figura de comparação"):
            fig_comparacao = _executar(
                "_figura_comparacao",
                base._figura_comparacao,
                painel, grupo, codigos, ano, dependencia, disciplina,
                nomes_selecionados, referencia,
                serie_participantes=serie_part,
            )
        _marcar("após figura comparação", figura=fig_comparacao)

        with etapa("análise: dispersão + regressão (statsmodels)"):
            dispersao_resultado = _executar(
                "_figura_dispersao",
                base._figura_dispersao,
                painel, grupo, ano, dependencia, disciplina, nomes,
                codigos_destaque=codigos,
            )
        if isinstance(dispersao_resultado, tuple):
            fig_dispersao, resumo_corr = dispersao_resultado
        else:
            fig_dispersao, resumo_corr = dispersao_resultado, ""
        _marcar("após figura dispersão", figura=fig_dispersao)

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
        _marcar(
            "antes de retornar callback",
            painel=painel,
            grupo=grupo,
            serie_part=serie_part,
            serie_disc=serie_disc,
            fig_part=fig_part,
            fig_desempenho=fig_desempenho,
            fig_comparacao=fig_comparacao,
            fig_dispersao=fig_dispersao,
        )

        return (
            kpis, fig_part, fig_desempenho, resumo_tendencia_redacao,
            fig_comparacao, fig_dispersao, resumo
        )
