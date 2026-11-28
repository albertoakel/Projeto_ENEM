"""Execução isolada da página analise_municipal para diagnóstico de memória."""

from dash_utils.ram_isolado import executar_pagina

if __name__ == "__main__":
    executar_pagina("analise_municipal")
