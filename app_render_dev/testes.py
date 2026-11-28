from pathlib import Path
import os
import gc
import time
import json
import platform
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

data_hora = datetime.now()

print(data_hora.strftime("%d/%m/%Y %H:%M:%S"))

#registrar_print
#sys.stdout = os.popen(f'tee print_log.{ data_hora.strftime("%Y-%m-%d_%H-%M-%S")}', "w")

# Disponibilizar os módulos do projeto
root_dir = Path.cwd()
if root_dir.name != "app_render" and (root_dir / "app_render").is_dir():
    root_dir = root_dir / "app_render"

src_dir = root_dir / "dash_utils"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
#
# Importar a função atualizada
from dash_utils.features_names import read_allfiles2
#
try:
    import psutil
except ImportError:
    psutil = None

data_dir = root_dir / "data" / "consumo" / "uf=PA"

ARQUIVOS = {
    "painel": data_dir / "painel_municipal.parquet",
    "faixa": data_dir / "faixa_etaria_municipal.parquet",
    "grupo": data_dir / "desempenho_grupos_municipal.parquet",
    "dsp": data_dir/ "desempenho_sexo_faixa_etaria_municipal.parquet"}


print("-" * 90)
print('root_dir :',root_dir)
print('src_dir  :',src_dir)
#print('data_dir :',data_dir)

print("-" * 90)
print(f'INICIO')
print("-" * 90)

processo = psutil.Process()

gc.collect()
rss_antes = processo.memory_info().rss / 1024**2

inicio = time.perf_counter()
dados = read_allfiles2("PA", P=None)

#
tempo = time.perf_counter() - inicio
rss_depois = processo.memory_info().rss / 1024**2

memoria_tabelas = sum(
    dados[nome]["data"].memory_usage(deep=True).sum()
    for nome in ["painel", "faixa", "grupo", "dsp"]
) / 1024**2

print(f"Tempo de leitura: {tempo:.3f} s")
print(f"Memória dos DataFrames: {memoria_tabelas:.2f} MB")
print(f"RSS antes: {rss_antes:.2f} MB")
print(f"RSS depois: {rss_depois:.2f} MB")
print(f"Variação RSS: {rss_depois - rss_antes:.2f} MB")




from dash_utils.data_loader import (carregar_dados, limpar_cache_dados, status_cache_dados)
print("=" * 90)
print("PROCESSO 1")
print("=" * 90)

processo = psutil.Process()

# Limpar cache anterior
limpar_cache_dados()
gc.collect()
#
rss_antes = processo.memory_info().rss / 1024**2

# Primeira chamada: leitura do disco
inicio = time.perf_counter()
dados = carregar_dados("PA", referencia=None)
tempo_primeira = time.perf_counter() - inicio

rss_depois = processo.memory_info().rss / 1024**2

#-------------------------------------------------------------------------------------------
print("PRIMEIRA CHAMADA")
print(f"Tempo: {tempo_primeira:.3f} s")
print(f"RSS antes: {rss_antes:.2f} MB")
print(f"RSS depois: {rss_depois:.2f} MB")

print("\nLINHAS CARREGADAS")
for tabela in ["painel", "faixa", "grupo", "dsp"]:
    print(f"{tabela}: {len(dados[tabela]):,}")

# Segunda chamada: deve aproveitar o cache
inicio = time.perf_counter()
dados2 = carregar_dados("PA", referencia=None)
tempo_segunda = time.perf_counter() - inicio

print(f"\nSEGUNDA CHAMADA: {tempo_segunda:.4f} s")

print("\nSTATUS DO CACHE")
print(status_cache_dados())

#-------------------------------------------------------------------------------------------
print("=" * 90)
print("PROCESSO 2")
print("=" * 90)#
processo = psutil.Process()

print("VERSÃO DO PANDAS:", pd.__version__)

print("\nMEMÓRIA DOS OBJETOS")

for nome in ["painel", "faixa", "grupo", "dsp"]:
    df = dados[nome]

    memoria = df.memory_usage(deep=True).sum() / 1024**2

    print(
        f"{nome:8s} | "
        f"Linhas: {len(df):>9,} | "
        f"Colunas: {len(df.columns):>3} | "
        f"Memória: {memoria:8.2f} MB"
    )

shape = dados["shape"]

print(
    f"{'shape':8s} | "
    f"Linhas: {len(shape):>9,} | "
    f"Colunas: {len(shape.columns):>3} | "
    f"Memória: {shape.memory_usage(deep=True).sum() / 1024**2:8.2f} MB"
)

gc.collect()

print(f"\nRSS atual: "
      f"{processo.memory_info().rss / 1024**2:.2f} MB"
)


#-------------------------------------------------------------------------------------------
print("=" * 90)
print("PROCESSO 3")
print("=" * 90)#
for referencia in ["ESC", "PROVA"]:

    gc.collect()

    rss_antes = processo.memory_info().rss / 1024**2
    inicio = time.perf_counter()

    dados_teste = read_allfiles2("PA", P=referencia)

    tempo = time.perf_counter() - inicio
    rss_depois = processo.memory_info().rss / 1024**2

    memoria = sum(
        dados_teste[nome]["data"].memory_usage(deep=True).sum()
        for nome in ["painel", "faixa", "grupo", "dsp"]
    ) / 1024**2

    print(f"\nREFERÊNCIA: {referencia}")
    print(f"Tempo: {tempo:.3f} s")
    print(f"Memória dos DataFrames: {memoria:.2f} MB")
    print(f"Variação RSS: {rss_depois - rss_antes:.2f} MB")

    for nome in ["painel", "faixa", "grupo", "dsp"]:
        df = dados_teste[nome]["data"]
        print(f"{nome}: {len(df):,} linhas")

    del dados_teste



