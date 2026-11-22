# Dashboard ENEM

Aplicação interativa desenvolvida em **Dash** para exploração dos dados históricos do Exame Nacional do Ensino Médio (ENEM), com recortes estaduais e municipais, indicadores de participação, desempenho acadêmico, perfil dos participantes e distribuição territorial.

O dashboard consome os produtos da camada **Consumo** do pipeline de dados do Projeto ENEM e utiliza malhas municipais para produzir visualizações geográficas.

## 1. Funcionalidades

A aplicação possui quatro páginas integradas, acessíveis pelo menu de navegação.

### 1.1. Visão Geral

Apresenta um panorama histórico do ENEM na Unidade da Federação selecionada.

Principais conteúdos:

- Evolução anual do número de participantes;
- Participação segundo dependência administrativa;
- Evolução das médias de Redação;
- Desempenho na prova objetiva e nas quatro áreas de conhecimento;
- Comparação entre escolas públicas e privadas;
- Comparação entre as redes públicas municipal, estadual e federal.

As médias estaduais de desempenho são calculadas de forma ponderada pelo número de notas válidas dos municípios.

A página distingue os dois modelos de avaliação:
- **1998–2008:** prova objetiva e Redação, com escala de 0 a 100;
- **2009–2025:** Ciências da Natureza, Ciências Humanas, Linguagens, Matemática e Redação, com escala de 0 a 1000.

### 1.2. Mapas Municipais

Apresenta a distribuição espacial dos indicadores selecionados para os municípios da UF.

Filtros disponíveis:

- Ano;
- Indicador;
- Dependência administrativa.

Indicadores disponíveis conforme o período:
- Número de participantes (1998–2025);
- Redação (1998–2025);
- Prova objetiva (1998–2008);
- Ciências da Natureza (2009–2025);
- Ciências Humanas (2009–2025);
- Linguagens (2009–2025);
- Matemática (2009–2025).

A página reúne:

- Mapa coroplético municipal;
- Ranking dos cinco municípios com maiores valores;
- Indicadores agregados;
- Estatísticas municipais;
- Histograma da distribuição dos valores;
- Boxplot da dispersão municipal.

Para os indicadores de desempenho, a dependência administrativa não está disponível antes de 2001.

**Critério de cobertura:** os municípios com até 100 notas válidas não recebem valor temático no mapa nem integram as estatísticas de desempenho. O objetivo é explicitar a cobertura amostral e evitar interpretações baseadas em quantitativos reduzidos.

### 1.3. Análise Municipal

Permite investigar individualmente um município e compará-lo com outros municípios da mesma UF.

Filtros disponíveis:

- Município principal;
- Até quatro municípios para comparação;
- Dependência administrativa;
- Indicador de desempenho;
- Ano de referência.

Análises apresentadas:

- Evolução histórica do número de participantes;
- Evolução das médias de desempenho;
- Indicadores de participação e desempenho para o ano selecionado;
- Comparação entre municípios;
- Relação entre número de notas válidas e desempenho;
- Dispersão dos resultados e análise de correlação;
- Estimativas de tendências por regressão linear.

Para a Redação, a análise de tendências considera separadamente os períodos anterior e posterior a 2009, além de um modelo com variável indicadora para representar a mudança de nível associada à transição.

As tendências e associações apresentadas são descritivas e não devem ser interpretadas como relações causais.

### 1.4. Perfil dos Participantes

Investiga a composição sociodemográfica dos participantes e sua relação com o desempenho nas avaliações.

Filtros disponíveis:

- Ano de referência;
- Avaliação.

Principais conteúdos:

- Evolução da participação por sexo;
- Evolução da distribuição por faixa etária;
- Desempenho por sexo;
- Distribuição dos participantes por faixa etária;
- Pirâmide de sexo e faixa etária;
- Desempenho cruzado por sexo e faixa etária;
- Indicadores de cobertura e quantidade de participantes.

As faixas etárias são organizadas em cinco categorias, conforme o mapeamento definido no projeto. Os códigos originais de `TP_FAIXA_ETARIA` são índices, não idades.

Os gráficos de desempenho utilizam médias ponderadas pelo número de notas válidas. Quando aplicável, são apresentados intervalos de confiança de 95%.

O produto de desempenho cruzado por sexo e faixa etária possui disponibilidade histórica até 2023. Anos sem dados não são interpolados.

## 2. Filtros globais

Duas seleções são compartilhadas pelas páginas:

| Filtro | Opções |
|---|---|
| Unidade da Federação | 27 UFs brasileiras |
| Referência territorial | Escola (ESC) ou Local de prova (PROVA) |

A aplicação inicia com:
- UF padrão: `PA`;
- Referência territorial: `ESC`.

A referência territorial determina o recorte municipal utilizado na exploração dos dados.

## 3. Arquitetura da aplicação

A aplicação está organizada em módulos, separando a inicialização do Dash, as páginas, o carregamento dos dados e os recursos auxiliares.

```text
dash/
├── app.py
├── assets/
├── components/
├── dash_utils/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── perf.py
│   └── ufs.py
├── pages/
│   ├── __init__.py
│   ├── visao_geral.py
│   ├── visao_geral_layout.py
│   ├── visao_geral_graficos.py
│   ├── mapa_geral.py
│   ├── analise_municipal.py
│   └── perfil_participantes.py
├── services/
└── __init__.py
```

### Organização dos módulos

| Módulo | Responsabilidade |
|---|---|
| `app.py` | Inicialização da aplicação, navegação, filtros globais e registro dos callbacks |
| `pages/visao_geral.py` | Coordenação da página Visão Geral e callbacks dos gráficos interativos |
| `pages/visao_geral_layout.py` | Estrutura visual da Visão Geral |
| `pages/visao_geral_graficos.py` | Preparação dos dados e construção dos gráficos da Visão Geral |
| `pages/mapa_geral.py` | Preparação dos indicadores municipais, mapas e estatísticas espaciais |
| `pages/analise_municipal.py` | Análises individuais e comparativas dos municípios |
| `pages/perfil_participantes.py` | Análises demográficas e de desempenho por grupos |
| `dash_utils/data_loader.py` | Leitura, filtragem e armazenamento temporário dos produtos de Consumo |
| `dash_utils/perf.py` | Instrumentação de desempenho e registros de execução |
| `dash_utils/ufs.py` | Dicionário de siglas e nomes das Unidades da Federação |

## 4. Origem e estrutura dos dados

O dashboard utiliza os produtos consolidados na camada **Consumo** do pipeline ENEM.

Para cada UF, são carregados os seguintes arquivos:

| Arquivo | Conteúdo |
|---|---|
| `painel_municipal.parquet` | Participação e indicadores municipais |
| `faixa_etaria_municipal.parquet` | Distribuição dos participantes por faixa etária |
| `desempenho_grupos_municipal.parquet` | Desempenho segundo grupos, incluindo dependência administrativa |
| `desempenho_sexo_faixa_etaria_municipal.parquet` | Desempenho cruzado por sexo e faixa etária |

Também é utilizada a malha municipal correspondente à UF, armazenada no diretório de shapefiles do projeto.

Estrutura esperada dos dados:

```text
data/
├── consumo/
│   ├── uf=PA/
│   │   ├── painel_municipal.parquet
│   │   ├── faixa_etaria_municipal.parquet
│   │   ├── desempenho_grupos_municipal.parquet
│   │   └── desempenho_sexo_faixa_etaria_municipal.parquet
│   └── ...
└── shapefiles/
    ├── PA_Municipios_2025/
    └── ...
```

O carregador utiliza a configuração central do projeto para localizar os diretórios de dados e os produtos de Consumo.

## 5. Desempenho e otimização

Foram implementados mecanismos para reduzir leituras repetidas e o custo de reconstrução das visualizações.

### Cache de dados

O módulo `data_loader.py` implementa:

- Cache dos dados carregados por UF;
- Cache dos dados filtrados por referência territorial;
- Limite de três UFs mantidas simultaneamente no cache principal;
- Cópias dos DataFrames entregues aos callbacks, protegendo os dados armazenados;
- Sincronização de leituras concorrentes para evitar carregamentos simultâneos desnecessários.

### Cache de layouts

O `app.py` utiliza cache para os layouts das páginas, considerando a combinação de página, UF e referência territorial.

### Cache geográfico

A página de mapas mantém o GeoJSON municipal em cache por UF. As geometrias são transformadas para EPSG:4326 e simplificadas antes da construção das figuras, reduzindo o volume de dados enviado ao navegador.

### Reutilização de cálculos

As páginas também reutilizam agregações e séries calculadas durante a atualização dos gráficos, evitando processamentos repetidos dentro de uma mesma interação.

## 6. Monitoramento de desempenho

O módulo `dash_utils/perf.py` registra no terminal:

- Tempo de execução de callbacks;
- Duração de etapas de carregamento;
- Tempo de construção de layouts;
- Tempo de preparação dos mapas e GeoJSON;
- Ocorrência de erros durante callbacks.

Os registros permitem identificar gargalos de leitura, processamento e renderização.

Variáveis de ambiente disponíveis:

```bash
# Execução normal, com registros de desempenho
python app.py

# Silenciar os registros de desempenho
ENEM_PERF=0 python app.py

# Exibir também argumentos dos callbacks
ENEM_PERF=2 python app.py

# Pré-carregar os dados e o GeoJSON da UF padrão
ENEM_PREAQUECER=1 python app.py
```

## 7. Tecnologias utilizadas

- **Python:** linguagem principal;
- **Dash:** estrutura da aplicação web;
- **Plotly:** gráficos interativos e mapas coropléticos;
- **Pandas:** manipulação e agregação dos dados;
- **NumPy:** operações numéricas;
- **GeoPandas:** leitura e manipulação das malhas geográficas;
- **Statsmodels:** modelos de regressão e análise estatística;
- **PyArrow:** suporte à leitura dos arquivos Parquet.

O dashboard também utiliza módulos internos do projeto, especialmente os responsáveis pela configuração dos diretórios, leitura dos dados e padronização das variáveis.

## 8. Execução local

A execução deve ocorrer no ambiente Python configurado para o Projeto ENEM, com as dependências da aplicação instaladas e os produtos de Consumo e shapefiles disponíveis.

A partir da raiz do projeto:

```bash
cd dash
python app.py
```

Por padrão, a aplicação é iniciada em:

```text
http://127.0.0.1:8050
```




## 9. Versão demo web
#### [Abrir aplicação* web ↗](https://dash-apps-2fay.onrender.com/)
\* versão limita a `UF=PA`




## 10. Considerações metodológicas

A interpretação dos resultados deve considerar as mudanças ocorridas na estrutura do ENEM ao longo do período analisado.

Entre 1998 e 2008, a avaliação contemplava prova objetiva e Redação. A partir de 2009, passou a contemplar quatro áreas de conhecimento e Redação, com mudanças nas escalas e nos critérios de avaliação.

Além disso, os dados apresentam diferenças de disponibilidade temporal, cobertura territorial e composição dos grupos analisados.

As médias municipais e estaduais são indicadores agregados. Portanto, os resultados descrevem padrões de participação e desempenho, mas não permitem, isoladamente, estabelecer relações causais.

## 11. Integração com o Projeto ENEM

O dashboard constitui a camada de visualização e exploração dos dados do Projeto ENEM.

Seu fluxo de consumo é:

```text
Microdados do ENEM
        │
        ▼
Pipeline de processamento
        │
        ▼
Camada Consumo
        │
        ├── Produtos Parquet por UF
        │
        └── Malhas municipais
                │
                ▼
          Dashboard Dash
                │
                ├── Visão Geral
                ├── Mapas Municipais
                ├── Análise Municipal
                └── Perfil dos Participantes
```

A separação entre processamento, armazenamento e visualização permite que o dashboard consuma produtos previamente estruturados, sem precisar executar novamente as etapas de transformação dos microdados.