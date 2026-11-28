# Dashboard ENEM — versão de produção candidata

Aplicação Dash para explorar participação, desempenho, distribuição territorial e perfil dos participantes do ENEM. Esta versão usa o loader otimizado e a página de análise com regressão OLS leve, sem importar Statsmodels.

## Estrutura dos dados

Cada UF fica em seu próprio diretório. Os quatro Parquets originais são preservados. Os oito arquivos preparados ficam juntos em `otimizado/`, com o nome indicando a base e a referência:

```text
data/
├── consumo/
│   └── uf=PA/
│       ├── desempenho_grupos_municipal.parquet
│       ├── desempenho_sexo_faixa_etaria_municipal.parquet
│       ├── faixa_etaria_municipal.parquet
│       ├── painel_municipal.parquet
│       └── otimizado/
│           ├── dsp_ESC.parquet
│           ├── dsp_PROVA.parquet
│           ├── faixa_ESC.parquet
│           ├── faixa_PROVA.parquet
│           ├── grupo_ESC.parquet
│           ├── grupo_PROVA.parquet
│           ├── painel_ESC.parquet
│           ├── painel_PROVA.parquet
│           └── manifest.json
└── shapefiles/
    └── PA_Municipios_2025/
        ├── PA_Municipios_2025.shp
        ├── PA_Municipios_2025.shx
        ├── PA_Municipios_2025.dbf
        ├── PA_Municipios_2025.prj
        └── PA_Municipios_2025.cpg
```

O pacote inicial contém os dados originais e o shapefile do Pará. Outras UFs podem ser adicionadas quando seus quatro Parquets originais e seu shapefile estiverem disponíveis.

## Preparar os Parquets de uma UF

O único programa de preparação fica na raiz do projeto: `preparar_consumo_dashboard.py`. Ele recebe obrigatoriamente a UF solicitada e não apresenta uma lista interativa de estados.

```bash
python preparar_consumo_dashboard.py --uf PA
```

Antes de processar, o programa verifica os quatro arquivos originais em `data/consumo/uf=PA/`:

- Se a pasta ou os dados originais não existirem, informa que eles ainda não foram disponibilizados/processados.
- Se algum dos quatro arquivos estiver ausente, informa exatamente quais estão faltando.
- Se os oito Parquets e o manifesto já existirem e estiverem registrados como preparados, informa que a UF já foi processada e não faz nada.
- Se houver uma preparação parcial, informa o estado e solicita `--force` para recriar o conjunto completo.

Para apenas verificar a UF e os arquivos de origem, sem gravar nada:

```bash
python preparar_consumo_dashboard.py --uf PA --dry-run
```

Para reprocessar uma UF já preparada:

```bash
python preparar_consumo_dashboard.py --uf PA --force
```

A transformação seleciona as colunas utilizadas pelo dashboard, normaliza `RESIDENCIA` para `ESC` e separa os registros `ESC` e `PROVA` em arquivos distintos. A gravação usa Row Groups de 100.000 linhas, compressão Snappy e dictionary encoding. Os tipos numéricos originais são preservados; o downcasting continua sendo aplicado pelo loader durante a leitura. Os detalhes de cada arquivo e da validação ficam registrados em `manifest.json`.

Cada arquivo é relido e validado por contagem de linhas, ordem das colunas e assinatura de conteúdo. Os arquivos são preparados temporariamente e promovidos como conjunto após a validação. Os quatro originais não são sobrescritos.

## Loader do dashboard

Para uma referência específica, o loader procura o arquivo correspondente em `data/consumo/uf=<UF>/otimizado/`, por exemplo `painel_ESC.parquet`. O conjunto otimizado só é utilizado quando os oito Parquets e o manifesto estão presentes e válidos.

Se ainda não houver preparação otimizada, o loader utiliza os Parquets originais e aplica os filtros de referência durante a leitura. Se encontrar um conjunto parcial ou um manifesto inválido, interrompe com uma mensagem para recriar os arquivos usando `--force`.

O dashboard continua limitado às UFs listadas em `ENEM_UFS_DISPONIVEIS`. No pacote inicial, o valor é `PA`; só inclua outra UF depois de disponibilizar também seus dados e shapefile.

## Instalação e execução local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Prepare os dados antes de testar o caminho otimizado.
python preparar_consumo_dashboard.py --uf PA

ARROW_DEFAULT_MEMORY_POOL=system \
ENEM_CACHE_MAX_ENTRIES=1 \
ENEM_UFS_DISPONIVEIS=PA \
python -m gunicorn app:server --bind 0.0.0.0:8050 --workers 1 --timeout 120
```

Acesse `http://127.0.0.1:8050`.

## Render

- **Root Directory:** pasta desta aplicação.
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:**

```bash
gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

Variáveis recomendadas:

| Variável | Valor inicial | Finalidade |
|---|---|---|
| `ARROW_DEFAULT_MEMORY_POOL` | `system` | Seleciona o Memory Pool do PyArrow |
| `ENEM_CACHE_MAX_ENTRIES` | `1` | Limita o cache de dados |
| `ENEM_UFS_DISPONIVEIS` | `PA` | Restringe as UFs disponíveis no deploy |
| `ENEM_UF_PADRAO` | `PA` | UF inicial |
| `ENEM_REFERENCIA_PADRAO` | `ESC` | Referência inicial |
| `ENEM_APPLY_DOWNCAST` | `1` | Habilita downcasting durante a leitura |
| `ENEM_HTTP_MEMORY_LOG` | `1` | Registra RSS/USS após callbacks HTTP |
| `ENEM_RAM_LOG` | `0` | Ativa logs detalhados da Visão Geral quando `1` |

## Dependências

`statsmodels`, `matplotlib`, `seaborn` e `ipython` não fazem parte das dependências de runtime desta versão. A regressão da página Análise utiliza NumPy e SciPy. PyArrow, GeoPandas e Plotly permanecem necessários.

## Situação da validação

O pacote inclui os quatro Parquets originais e os arquivos do shapefile do Pará. A geração dos oito Parquets otimizados deve ser executada no ambiente do projeto com as dependências instaladas, usando o comando acima, antes do deploy otimizado.
