#visao_geral.py
from dash import Input, Output, State, callback
from dash_utils.perf import etapa, medir_callback

from .visao_geral_graficos import criar_graficos, criar_grafico_area_selecionada
from .visao_geral_layout import criar_layout as montar_layout


@callback(
    Output("grafico-pp-area", "figure"),
    Input("seletor-pp-area", "value"),
    State("dados-pp-areas", "data")
)
@medir_callback("visão geral · gráfico público x privado")
def atualizar_grafico_publico_privado(disciplina, registros):
    return criar_grafico_area_selecionada(
        registros=registros,
        disciplina=disciplina,
        comparacao="publico_privado"
    )


@callback(
    Output("grafico-redes-publicas-area", "figure"),
    Input("seletor-redes-publicas-area", "value"),
    State("dados-redes-publicas-areas", "data")
)
@medir_callback("visão geral · gráfico redes públicas")
def atualizar_grafico_redes_publicas(disciplina, registros):
    return criar_grafico_area_selecionada(
        registros=registros,
        disciplina=disciplina,
        comparacao="redes_publicas"
    )


def criar_layout(dados):
    """Coordena a construção da página Visão Geral."""
    with etapa("visão geral: criar gráficos"):
        graficos = criar_graficos(dados)
    with etapa("visão geral: montar layout"):
        return montar_layout(dados, graficos)
