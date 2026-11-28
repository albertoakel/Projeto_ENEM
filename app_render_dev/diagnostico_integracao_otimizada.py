"""Teste local do loader otimizado. Execute da raiz de app_render."""
from pathlib import Path
import os
import gc
import json
import time

# Precisa ocorrer antes de importar dash_utils/features_names_otimizado.
os.environ["ARROW_DEFAULT_MEMORY_POOL"] = os.environ.get("ENEM_ARROW_MEMORY_POOL", "system")
os.environ.setdefault("ENEM_CACHE_MAX_ENTRIES", "1")

import psutil
from dash_utils.data_loader_otimizado import (
    carregar_dados,
    limpar_cache_dados,
    status_cache_dados,
)
from dash_utils.features_names_otimizado import status_loader_otimizado

UF = os.environ.get("ENEM_UF_PADRAO", "PA").strip().upper()
REFERENCIAS = ("ESC", "PROVA")
EXPECTED_ROWS_PA = {
    "ESC": {"painel": 3625, "faixa": 38335, "grupo": 186449, "dsp": 250436},
    "PROVA": {"painel": 1339, "faixa": 23177, "grupo": 131814, "dsp": 187444},
}
PROCESSO = psutil.Process()

print("Configuração:")
print(json.dumps(status_loader_otimizado(), indent=2, ensure_ascii=False))
if not status_loader_otimizado()["memory_pool_confirmado"]:
    raise RuntimeError("Memory Pool solicitado não corresponde ao backend real.")

for referencia in REFERENCIAS:
    limpar_cache_dados()
    gc.collect()
    memoria_ini = PROCESSO.memory_full_info()
    inicio = time.perf_counter()
    dados = carregar_dados(UF, referencia=referencia)
    duracao = time.perf_counter() - inicio
    memoria_fim = PROCESSO.memory_full_info()

    print(f"\nUF={UF} | referência={referencia} | tempo={duracao:.3f}s")
    for base in ("painel", "faixa", "grupo", "dsp"):
        df = dados[base]
        linhas = len(df)
        deep_mb = df.memory_usage(deep=True).sum() / 1024**2
        print(f"{base:8s} shape={df.shape} deep={deep_mb:.2f} MB")
        if UF == "PA" and linhas != EXPECTED_ROWS_PA[referencia][base]:
            raise AssertionError(
                f"Contagem divergente em {base}/{referencia}: "
                f"esperado={EXPECTED_ROWS_PA[referencia][base]}, obtido={linhas}"
            )

    print(
        "Memória processo: "
        f"RSS={memoria_fim.rss / 1024**2:.1f} MB | "
        f"USS={getattr(memoria_fim, 'uss', 0) / 1024**2:.1f} MB | "
        f"delta USS={(getattr(memoria_fim, 'uss', 0) - getattr(memoria_ini, 'uss', 0)) / 1024**2:.1f} MB"
    )
    print("Cache:", status_cache_dados())
    del dados
    limpar_cache_dados()
    gc.collect()

print("\nTESTE DO LOADER OTIMIZADO CONCLUÍDO.")
