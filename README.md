# Projeto ENEM — Análise histórica, territorial e educacional

Projeto de **Engenharia e Análise de Dados** dos microdados do Exame Nacional do Ensino Médio (ENEM), abrangendo as edições de **1998 a 2025**.

O projeto organiza e harmoniza dados de diferentes edições do exame, produz indicadores agregados por município e ano e disponibiliza os resultados em estudos analíticos e em um dashboard interativo.

O processamento é estruturado por Unidade da Federação (UF), permitindo trabalhar com diferentes recortes geográficos e temporais, conforme a disponibilidade das fontes.

A proposta integra Engenharia de Dados, Análise Exploratória, Estatística e Visualização de Dados para investigar a evolução da participação, o perfil dos participantes e as desigualdades de desempenho no ENEM.

## Objetivos

- Organizar os microdados históricos do ENEM em uma estrutura de dados padronizada.
- Harmonizar variáveis e referências territoriais que mudaram ao longo das edições.
- Produzir indicadores municipais de participação, perfil dos participantes e desempenho.
- Explorar padrões temporais e espaciais por meio de análises transversais e longitudinais.
- Investigar desigualdades relacionadas a gênero, idade, dependência administrativa e território.
- Disponibilizar os resultados em um dashboard interativo.
- Manter a rastreabilidade do processamento por meio de manifestos, relatórios e auditorias.

## Visão geral do projeto

O fluxo de dados segue uma arquitetura em camadas, baseada no padrão Medalhão:

```text
              Microdados oficiais do ENEM
                         |
                         v
                  Bronze / Staging
                         |
                         v
                       Silver
                         |
                         v
                        Gold
                         |
                         v
                      Analytic
                         |
                         v
                      Consumo
                         |
                    +----+----+
                    |         |
                    v         v
               Estudos    Dashboard
              Analíticos    Dash
```

| Camada | Responsabilidade |
|---|---|
| **Bronze** | Armazenamento e inventário dos arquivos originais compactados. |
| **Staging** | Extração temporária dos arquivos necessários ao processamento. |
| **Silver** | Seleção das variáveis de interesse e dos registros da UF. |
| **Gold** | Padronização do esquema e das referências territoriais. |
| **Analytic** | Geração de indicadores e estatísticas agregados por município. |
| **Consumo** | Integração e organização dos produtos para análises e visualizações. |

A documentação técnica detalha as regras, os formatos, as validações e os produtos de cada etapa.

## Produtos e análises

### Produtos de dados

A camada Analytic gera nove produtos analíticos relacionados a:

- Demografia dos participantes;
- Distribuição por faixa etária;
- Presença no exame;
- Desempenho em redação;
- Desempenho na prova objetiva, quando aplicável;
- Desempenho por área do conhecimento;
- Características das escolas;
- Desempenho por grupos;
- Desempenho por sexo e faixa etária, quando existe suporte nos dados de origem.

A camada Consumo organiza quatro produtos destinados à exploração:

- `painel_municipal`;
- `faixa_etaria_municipal`;
- `desempenho_grupos_municipal`;
- `desempenho_sexo_faixa_etaria_municipal`.

### Estudos analíticos

A partir dos produtos da camada Consumo, foram desenvolvidos oito estudos independentes, organizados por questões de pesquisa.

| Eixo | Investigação | Notebook |
|---|---|---|
| Q1 | Evolução da participação no ENEM | [Q1 — Participação](notebook/estudos_analiticos/Q1_EVOLUCAO_DA_PARTICIPACAO.ipynb) |
| Q2 | Desigualdade de gênero | [Q2 — Gênero](notebook/estudos_analiticos/Q2_DESIGUALDADE_DE_GENERO.ipynb) |
| Q3 | Desempenho por dependência administrativa | [Q3 — Dependência](notebook/estudos_analiticos/Q3_DESEMPENHO_DEPENDENCIA.ipynb) |
| Q4 | Idade e trajetória dos participantes | [Q4 — Idade](notebook/estudos_analiticos/Q4_IDADE_TRAJETORIA.ipynb) |
| Q5 | Desigualdade territorial | [Q5 — Território](notebook/estudos_analiticos/Q5_DESIGUALDADE_TERRITORIAL.ipynb) |
| Q6 | Distribuição e desigualdade do desempenho | [Q6 — Distribuição](notebook/estudos_analiticos/Q6_DISTRIBUICAO_DESEMPENHO.ipynb) |
| Q7 | Relações entre participação, perfil e desempenho | [Q7 — Participação e perfil](notebook/estudos_analiticos/Q7_PARTICIPACAO_PERFIL_DESEMPENHO.ipynb) |
| Q8 | Perfis multidimensionais de desempenho municipal | [Q8A — Método](notebook/estudos_analiticos/Q8A_CLUSTERINGS_METODO.ipynb) · [Q8B — Aplicação](notebook/estudos_analiticos/Q8B_CLUSTERINGS_APLICACAO.ipynb) |

Os estudos abordam diferentes dimensões do exame:

- Evolução histórica e distribuição territorial da participação;
- Diferenças de participação e desempenho entre homens e mulheres;
- Desigualdades entre redes de ensino;
- Mudanças na composição etária dos participantes;
- Distribuição territorial e evolução do desempenho municipal;
- Variabilidade e dispersão das notas;
- Relações entre participação, composição dos participantes e desempenho;
- Identificação e caracterização de perfis municipais multidimensionais de desempenho nas cinco disciplinas do ENEM.

O Q8 está dividido em dois notebooks complementares: o Q8A apresenta a comparação metodológica dos algoritmos de agrupamento, a avaliação de estabilidade e a seleção do K-Means com K=2; o Q8B aplica o método aos 37 municípios da coorte balanceada, em 15 edições (2009–2023), caracterizando os perfis, sua distribuição e as transições entre os extremos do período.

As investigações são predominantemente descritivas e utilizam indicadores estatísticos, comparações temporais, análises de distribuição, correlações, métodos de agrupamento e visualizações.

Os estudos não constituem avaliações causais de políticas públicas. Seus resultados oferecem evidências descritivas sobre a participação e o desempenho no ENEM, contribuindo para a compreensão das desigualdades educacionais.

**Documentação dos estudos:** [Estudos Analíticos — README](notebook/estudos_analiticos/README.md).

## Dashboard interativo

O projeto inclui uma aplicação desenvolvida com **Dash**, com quatro páginas:

1. **Visão Geral** — indicadores históricos de participação e desempenho;
2. **Mapas Municipais** — visualizações temáticas e comparações territoriais;
3. **Análise Municipal** — evolução e comparação entre municípios;
4. **Perfil dos Participantes** — distribuições por sexo e faixa etária e cruzamentos disponíveis.

A aplicação utiliza os produtos da camada Consumo e arquivos geográficos municipais.

Há mecanismos de cache e instrumentação de desempenho para reduzir carregamentos repetidos e acompanhar a execução.

## Tecnologias

- Python
- DuckDB
- Pandas
- NumPy
- PyArrow
- Parquet / Zstandard
- Jupyter Notebook
- Matplotlib
- Seaborn
- Dash
- Plotly
- GeoPandas
- Folium
- Shapefiles

## Estrutura do repositório

```text
Projeto_ENEM/
│
├── data/
│   ├── bronze/
│   ├── staging/
│   ├── silver/
│   ├── gold/
│   ├── analytic/
│   ├── consumo/
│   ├── metadata/
│   ├── reports/
│   └── shapefiles/
│
├── dash/
│   ├── app.py
│   ├── assets/
│   ├── components/
│   ├── dash_utils/
│   └── pages/
│
├── docs/
│   ├── DOCUMENTACAO_PROJETO.md
│   └── DOCUMENTACAO_MEDALHAO.md
│
├── notebook/
│   ├── README.md
│   │
│   ├── pipeline/
│   │   ├── README.md
│   │   ├── 00_Download_data_ENEM.ipynb
│   │   ├── 01_Verificar_configuracao.ipynb
│   │   ├── 02_Execucao_Silver.ipynb
│   │   ├── 03_Execucao_Gold.ipynb
│   │   ├── 04_Execucao_Analitico.ipynb
│   │   ├── 05_Execucao_Consumo.ipynb
│   │   ├── 06_Analise_transversal.ipynb
│   │   ├── 07_Analise_transversal_mapas.ipynb
│   │   ├── 08_Analise_longitudinal.ipynb
│   │   ├── 09a_Analise_longitudinal_mapas.ipynb
│   │   ├── 09b_Analise_longitudinal_mapas_folium.ipynb
│   │   ├── 10_auditoria_integrada_final.ipynb
│   │   ├── list_variables_consumo.ipynb
│   │   └── _setup.py
│   │
│   └── estudos_analiticos/
│       ├── README.md
│       ├── Q1_EVOLUCAO_DA_PARTICIPACAO.ipynb
│       ├── Q2_DESIGUALDADE_DE_GENERO.ipynb
│       ├── Q3_DESEMPENHO_DEPENDENCIA.ipynb
│       ├── Q4_IDADE_TRAJETORIA.ipynb
│       ├── Q5_DESIGUALDADE_TERRITORIAL.ipynb
│       ├── Q6_DISTRIBUICAO_DESEMPENHO.ipynb
│       ├── Q7_PARTICIPACAO_PERFIL_DESEMPENHO.ipynb
│       ├── Q8A_CLUSTERINGS_METODO.ipynb
│       ├── Q8B_CLUSTERINGS_APLICACAO.ipynb
│       └── _setup2.py
│
├── src/
│   ├── enem_pipeline/
│   └── utils/
│
├── executar_pipeline.py
├── executar_pipeline_lista.py
├── README.md
└── LICENSE
```

Os diretórios de dados armazenam arquivos de origem, produtos intermediários e resultados processados. Os dados são organizados por UF e, conforme a etapa, por ano, base de origem ou referência territorial.

## Como executar

### 1. Preparar o ambiente

Utilize um ambiente Python com as dependências do projeto instaladas.

Os módulos de processamento e o dashboard dependem das bibliotecas listadas na seção [Tecnologias](#tecnologias).

As versões e a instalação detalhada das dependências devem ser conferidas na configuração atual do repositório.

### 2. Disponibilizar os microdados

Coloque os arquivos compactados oficiais do ENEM no diretório:

```text
data/bronze/
```

O inventário do pipeline reconhece arquivos no padrão:

```text
microdados_enem_AAAA.zip
```

Substitua `AAAA` pelo ano da edição. Os arquivos correspondentes a todos os anos do intervalo solicitado precisam estar disponíveis antes da execução.

**O orquestrador não realiza o download automático dos microdados.**

O download também pode ser realizado pelo notebook `00_Download_data_ENEM.ipynb`, localizado em `notebook/pipeline/`.

### 3. Executar o pipeline

Na raiz do projeto:

```bash
python executar_pipeline.py
```

O script solicita:

- Sigla da UF;
- Ano inicial;
- Ano final.

Em seguida, executa as etapas de processamento e geração dos produtos. Ao final, os metadados e relatórios são registrados nos diretórios configurados do projeto.

Também está disponível o script `executar_pipeline_lista.py` para execução em lote, conforme sua configuração.

### 4. Executar o dashboard

Depois de gerar os produtos da camada Consumo e disponibilizar os shapefiles necessários, entre no diretório `dash/` e execute:

```bash
python app.py
```

Na configuração local atual, a aplicação é iniciada em:

```text
http://127.0.0.1:8050
```
### Versão demo web
#### [Abrir aplicação* web ↗](https://dash-apps-2fay.onrender.com/)
\* versão limita a `UF=PA`

### 5. Utilizar os notebooks

Os notebooks estão divididos em dois conjuntos:

**Pipeline de dados**

Diretório: `notebook/pipeline/`

Reúne os notebooks de configuração, obtenção dos dados, execução das camadas, análises transversais e longitudinais e auditoria integrada.

[Consultar documentação do pipeline](notebook/pipeline/README.md).

**Estudos analíticos**

Diretório: `notebook/estudos_analiticos/`

Reúne os oito estudos organizados por questões de pesquisa. Os notebooks Q1–Q7 podem ser executados independentemente. O Q8 é composto por dois notebooks complementares: Q8A (método) e Q8B (aplicação). A execução do Q8B depende dos resultados e do método definidos no Q8A, além dos produtos de Consumo necessários.

[Consultar documentação dos estudos analíticos](notebook/estudos_analiticos/README.md).

Para conhecer a organização geral dos notebooks, consulte o [README da pasta notebook](notebook/README.md).

## Cuidados metodológicos

A série histórica do ENEM não possui estrutura inteiramente uniforme. Algumas mudanças importantes precisam ser consideradas na leitura dos resultados:

- **Referências territoriais:** entre 1998 e 2000, a referência utilizada é o município de residência; entre 2001 e 2007, o município da escola; a partir de 2008, são trabalhadas as referências de escola e prova, conforme a disponibilidade das fontes. Residência, escola e local de prova são perspectivas diferentes e não devem ser tratadas como equivalentes.
- **Seleção por UF:** a partir de 2008, a seleção de registros na camada Silver utiliza a UF do local de prova. A perspectiva `ESC` gerada posteriormente não implica um novo filtro pela UF da escola.
- **Estrutura das notas:** até 2008, é utilizada a nota objetiva; a partir de 2009, o desempenho é representado pelas quatro áreas do conhecimento, além da redação. Comparações entre esses períodos exigem cautela.
- **Edições de 2024 e 2025:** os dados de participantes e resultados são processados em bases separadas. Não é realizado cruzamento individual entre essas fontes; por isso, alguns indicadores cruzados por sexo e faixa etária podem não estar disponíveis nessas edições.
- **Dados agregados:** os produtos municipais são estatísticas agregadas e não devem ser interpretados como observações individuais.
- **Perfis de agrupamento (Q8):** o K-Means é ajustado separadamente em cada edição, com padronização anual das cinco disciplinas. Os perfis A e B representam posições relativas dentro de cada edição: Perfil A corresponde ao grupo de maior desempenho multidisciplinar relativo e Perfil B ao de menor desempenho. A composição dos grupos pode variar entre anos; portanto, as médias por perfil não representam necessariamente a trajetória de um conjunto fixo de municípios.
---
## Uso de inteligência artificial no desenvolvimento

O desenvolvimento do projeto contou com o apoio de ferramentas de Inteligência
Artificial Generativa, especialmente modelos de linguagem de grande escala (LLMs), 
na assistência à elaboração, revisão e otimização de códigos, documentação.
A utilização dessas ferramentas ocorreu de forma assistiva, 
mantendo sob responsabilidade do desenvolvedor as decisões metodológicas, e direcionamentos
do projeto .
