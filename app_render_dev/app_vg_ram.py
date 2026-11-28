"""Execução isolada da página visao_geral para diagnóstico de memória."""

from dash_utils.ram_isolado import executar_pagina

if __name__ == "__main__":
    executar_pagina("visao_geral")
