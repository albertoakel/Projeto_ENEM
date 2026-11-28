# Dashboard ENEM — teste experimental com cache de layout 1

## Objetivo

Comparar o comportamento de memória da integração otimizada usando somente um layout em cache. A única mudança de comportamento em relação à versão `app_otimizado_cache_controlado.py` é `@lru_cache(maxsize=1)`. Também foi acrescentada medição de RSS/USS no ciclo HTTP do Dash, depois que a resposta do callback é produzida.

## Arquivos

- `app_otimizado_cache1.py`: nova entrada experimental.
- `dash_utils/data_loader_otimizado.py`: loader experimental do pacote anterior.
- `dash_utils/features_names_otimizado.py`: leitura otimizada do pacote anterior.
- `diagnostico_integracao_otimizada.py`: diagnóstico independente do loader.

Não sobrescreve `app.py`, `dash_utils/perf.py`, `dash_utils/data_loader.py` nem `dash_utils/features_names.py`. Os dois módulos `*_otimizado.py` são arquivos experimentais já usados na integração anterior.

## Instalação

Extraia o ZIP na raiz de `app_render`, mantendo a estrutura de pastas. Se os módulos `dash_utils/*_otimizado.py` já estiverem presentes a partir do pacote anterior, a versão incluída é a mesma utilizada naquela integração.

## Execução

```bash
ARROW_DEFAULT_MEMORY_POOL=system \
ENEM_CACHE_MAX_ENTRIES=1 \
python -m gunicorn app_otimizado_cache1:server \
  --bind 127.0.0.1:8050 \
  --workers 1 \
  --timeout 120
```

Navegue pelas mesmas quatro páginas, primeiro ESC e depois PROVA. Observe:

- `MEMORIA LAYOUT`: deve mostrar `maxsize=1` e `currsize` no máximo 1.
- `MEMORIA CALLBACK HTTP`: RSS/USS no início e no fim de cada requisição de callback, incluindo o status HTTP.
- `CACHE LAYOUT LIMPO`: comportamento na troca ESC/PROVA.

Compare com o teste anterior. Não altere a configuração do loader durante esta comparação.
