# Integração experimental — Dashboard ENEM otimizado

Este pacote acrescenta uma entrada alternativa para testar a configuração aprovada no Diagnóstico 08. **Não substitui `app.py`, `dash_utils/features_names.py` ou `dash_utils/data_loader.py`.**

## Arquivos incluídos

- `app_otimizado.py`: entrada alternativa do Dash; define `ARROW_DEFAULT_MEMORY_POOL` antes de importar os módulos do projeto.
- `dash_utils/features_names_otimizado.py`: leitura com `use_threads=False`, `read_dictionary=True`, Parquets separados por referência para PA e downcasting numérico.
- `dash_utils/data_loader_otimizado.py`: loader/cache alternativo; mantém uma única combinação UF/referência em memória por padrão.
- `diagnostico_integracao_otimizada.py`: teste local de carregamento ESC e PROVA, um por vez.

## Pré-requisito dos Parquets separados

O loader otimizado espera os arquivos gerados pelo Diagnóstico 07 neste layout:

```text
app_render/
└── _diagnosticos_memoria_07/
    └── parquet_variants/
        ├── painel/separado_rg_100000/ESC.parquet
        ├── painel/separado_rg_100000/PROVA.parquet
        ├── faixa/separado_rg_100000/ESC.parquet
        ├── faixa/separado_rg_100000/PROVA.parquet
        ├── grupo/separado_rg_100000/ESC.parquet
        ├── grupo/separado_rg_100000/PROVA.parquet
        ├── dsp/separado_rg_100000/ESC.parquet
        └── dsp/separado_rg_100000/PROVA.parquet
```

Se o diretório estiver em outro local, defina `ENEM_PARQUET_VARIANT_DIR` para apontar diretamente para `parquet_variants`.

## Instalação

Extraia o ZIP na raiz da cópia `app_render` que já contém `app.py`, `dash_utils/` e `pages/`. A extração apenas adiciona os novos arquivos; não sobrescreve os módulos originais.

## Primeiro teste — sem Gunicorn

Na raiz `app_render`, com o ambiente conda do projeto ativado:

```bash
ARROW_DEFAULT_MEMORY_POOL=system python diagnostico_integracao_otimizada.py
```

Se as variantes estiverem fora do caminho padrão:

```bash
ARROW_DEFAULT_MEMORY_POOL=system \
ENEM_PARQUET_VARIANT_DIR="/caminho/para/parquet_variants" \
python diagnostico_integracao_otimizada.py
```

O teste carrega ESC e PROVA sequencialmente, limpa o cache entre as referências e verifica as contagens conhecidas do PA. Se falhar, não avance para Gunicorn: envie o traceback e o log.

## Segundo teste — Dash com um worker

Somente depois de o teste anterior passar:

```bash
ARROW_DEFAULT_MEMORY_POOL=system \
ENEM_CACHE_MAX_ENTRIES=1 \
python -m gunicorn app_otimizado:server \
  --bind 127.0.0.1:8050 \
  --workers 1 \
  --timeout 120
```

Acesse `http://127.0.0.1:8050` e teste as quatro páginas, primeiro com ESC e depois PROVA. Observe o terminal e o consumo de memória.

## Ajustes opcionais

- `ENEM_APPLY_DOWNCAST=0`: desativa o downcasting sem alterar os Parquets.
- `ENEM_CACHE_MAX_ENTRIES=1`: mantém uma referência por vez (padrão recomendado para a primeira integração).
- `ENEM_PARQUET_VARIANT_DIR`: altera o diretório das variantes do Diagnóstico 07.
- `ENEM_UF_PADRAO=PA`: define a UF inicial.

Para voltar ao dashboard original, use normalmente `python app.py` ou `gunicorn app:server`. Os arquivos originais permanecem intactos.
