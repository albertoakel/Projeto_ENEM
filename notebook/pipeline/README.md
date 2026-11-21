# Pipeline de Dados — Projeto ENEM

## 1. Visão geral

Esta pasta reúne os notebooks responsáveis pela preparação, processamento, transformação, disponibilização e análise dos microdados históricos do Exame Nacional do Ensino Médio (ENEM).

O pipeline foi desenvolvido com base na arquitetura Medalhão, organizando o processamento em camadas que permitem transformar os microdados originais disponibilizados pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP) em produtos estruturados para análises estatísticas, temporais e espaciais.

O projeto contempla a série histórica de **1998 a 2025**, considerando as mudanças estruturais ocorridas ao longo das edições do exame.

O processamento é parametrizado por Unidade da Federação (UF), permitindo executar as etapas para diferentes estados brasileiros, mantendo os dados organizados e isolados territorialmente.

## 2. Organização do pipeline

O fluxo de processamento está organizado nas seguintes etapas:

1. Obtenção dos microdados originais;
2. Preparação e validação dos arquivos;
3. Processamento das camadas Silver e Gold;
4. Construção dos produtos Analytic e Consumo;
5. Análises estatísticas e espaciais;
6. Auditoria integrada dos produtos gerados.

### Arquitetura de dados

| Camada | Responsabilidade |
|---|---|
| Bronze | Armazenamento dos arquivos originais compactados disponibilizados pelo INEP. |
| Staging | Extração e preparação dos arquivos CSV necessários ao processamento. |
| Silver | Seleção, organização e estruturação dos microdados por UF e edição do ENEM. |
| Gold | Padronização e compatibilização dos dados, incluindo as referências territoriais. |
| Analytic | Construção de produtos analíticos agregados e estruturados para investigação. |
| Consumo | Disponibilização de produtos finais destinados às análises e aplicações. |

Os produtos intermediários e finais são armazenados predominantemente em formato Parquet. Catálogos, manifestos e relatórios de auditoria são utilizados para registrar a organização, a cobertura e a integridade dos dados.

## 3. Estrutura dos notebooks

Os notebooks estão organizados sequencialmente, de acordo com suas responsabilidades.

### 3.1 Preparação e configuração

| Notebook | Descrição |
|---|---|
| `00_Download_data_ENEM.ipynb` | Automatiza o download dos microdados do ENEM disponibilizados pelo INEP. Verifica a existência dos arquivos ZIP na Bronze antes de realizar novos downloads. |
| `01_Verificar_configuracao.ipynb` | Verifica as configurações do projeto, a estrutura dos diretórios, o inventário Bronze, os arquivos compactados, a extração para Staging, os catálogos de variáveis e a leitura dos CSVs com DuckDB. |

**Observação:** o intervalo de download atualmente configurado no notebook 00 contempla 1998–2000. O período pode ser alterado diretamente em seus parâmetros.

### 3.2 Processamento das camadas Medalhão

| Notebook | Descrição |
|---|---|
| `02_Execucao_Silver.ipynb` | Executa o processamento dos microdados para a UF selecionada, produzindo os arquivos Parquet da camada Silver. |
| `03_Execucao_Gold.ipynb` | Executa a transformação Silver → Gold, aplicando a padronização dos esquemas e das referências territoriais. Produz os arquivos Parquet e o manifesto Gold. |
| `04_Execucao_Analitico.ipynb` | Constrói nove produtos analíticos a partir da camada Gold, realizando agregações e validações. Gera os arquivos Parquet, catálogo e manifesto Analytic. |
| `05_Execucao_Consumo.ipynb` | Constrói quatro produtos de consumo a partir da camada Analytic, gerando os arquivos Parquet, catálogo, manifesto e auditoria da camada. |

As regras de transformação e processamento estão centralizadas nos módulos Python do pacote `enem_pipeline`, localizado em `src/`. Os notebooks são responsáveis por configurar, executar, acompanhar e validar essas rotinas.

### 3.3 Análises estatísticas e espaciais

Os notebooks seguintes utilizam os produtos da camada Consumo para investigar características da participação e do desempenho no ENEM.

| Notebook | Descrição |
|---|---|
| `06_Analise_transversal.ipynb` | Desenvolve uma análise transversal dos indicadores municipais para um ano selecionado, considerando participação, desempenho, dependência administrativa, sexo e faixa etária. |
| `07_Analise_transversal_mapas.ipynb` | Apresenta a distribuição espacial dos indicadores municipais para um ano selecionado, por meio de mapas temáticos. |
| `08_Analise_longitudinal.ipynb` | Investiga a evolução temporal da participação e do desempenho municipal, incluindo tendências, diferenças entre grupos, estabilidade das posições municipais e rankings. |
| `09a_Analise_longitudinal_mapas.ipynb` | Apresenta a evolução espacial dos indicadores por meio de mapas de referência, variação e tendência municipal. |
| `09b_Analise_longitudinal_mapas_folium.ipynb` | Desenvolve representações cartográficas interativas utilizando Folium, incluindo mapas de referência, variação e tendência. |

As análises são realizadas respeitando a disponibilidade temporal das variáveis e as mudanças metodológicas ocorridas na estrutura do ENEM.

**Compatibilidade temporal:** os indicadores de desempenho são analisados em dois períodos independentes:

- **1998–2008:** prova objetiva e redação segundo a estrutura antiga;
- **2009–2025:** Ciências da Natureza (CN), Ciências Humanas (CH), Linguagens e Códigos (LC), Matemática (MT) e redação segundo a estrutura nova.

As duas versões da redação não são tratadas como uma série homogênea. Da mesma forma, a prova objetiva do período anterior a 2009 não é comparada diretamente às quatro áreas de conhecimento do período posterior.

### 3.4 Auditoria integrada

| Notebook | Descrição |
|---|---|
| `10_auditoria_integrada_final.ipynb` | Executa uma auditoria de leitura das camadas Gold, Analytic e Consumo, verificando arquivos, manifestos, catálogos, contagens, chaves e cobertura territorial. Consolida os resultados e exporta um relatório CSV. |

A auditoria não reprocessa os dados nem modifica os arquivos Parquet das camadas avaliadas. Sua única gravação é o relatório final de auditoria.

A aprovação representa o atendimento aos critérios implementados no notebook, não substituindo uma auditoria semântica completa das regras de negócio.

## 4. Parametrização territorial

O processamento das camadas Silver, Gold, Analytic e Consumo é realizado por Unidade da Federação.

A UF é definida nos parâmetros de execução de cada notebook, por meio da variável `UF_EXECUCAO`.

Exemplo:

```python
UF_EXECUCAO = "PA"
```

Para executar o processamento em outra UF, basta alterar o valor da variável e executar novamente o notebook, respeitando a disponibilidade das fontes exigidas pela etapa.

Os produtos são organizados em diretórios individualizados por UF, evitando a mistura de dados de diferentes unidades federativas.

Exemplo de organização:

```text
data/
├── bronze/
├── staging/
├── silver/
│   └── uf=PA/
├── gold/
│   └── uf=PA/
├── analytic/
│   └── uf=PA/
└── consumo/
    └── uf=PA/
```

Os diretórios de metadados mantêm os manifestos, catálogos e relatórios associados às respectivas execuções.

## 5. Configuração do ambiente

O arquivo `_setup.py` realiza a inicialização do ambiente utilizado pelos notebooks.

Suas responsabilidades incluem:

- Identificar o diretório de execução;
- Resolver o diretório raiz do projeto;
- Localizar o diretório `src/`;
- Adicionar `src/` ao `sys.path`, permitindo importar os módulos do pacote `enem_pipeline`.

Os módulos de configuração e processamento são importados diretamente dos componentes do projeto.

Entre as principais tecnologias utilizadas estão:

- Python;
- Pandas;
- NumPy;
- DuckDB;
- PyArrow;
- Matplotlib;
- Seaborn;
- GeoPandas;
- Folium.

O notebook `09b_Analise_longitudinal_mapas_folium.ipynb` utiliza adicionalmente Folium, Branca e python-dotenv, além da variável de ambiente `CARTO_BASEMAPS_API_KEY` para a configuração cartográfica utilizada.

## 6. Ordem recomendada de execução

Para uma execução completa, recomenda-se seguir a sequência:

| Ordem | Notebook | Finalidade |
|---|---|---|
| 1 | 00 | Obtenção dos microdados. |
| 2 | 01 | Verificação do ambiente, inventário, extração e preparação dos dados. |
| 3 | 02 | Construção da camada Silver. |
| 4 | 03 | Construção da camada Gold. |
| 5 | 04 | Construção da camada Analytic. |
| 6 | 05 | Construção da camada Consumo. |
| 7 | 06 | Análise transversal. |
| 8 | 07 | Análise espacial transversal. |
| 9 | 08 | Análise longitudinal. |
| 10 | 09a | Análise longitudinal espacial. |
| 11 | 09b | Análise longitudinal espacial interativa. |
| 12 | 10 | Auditoria integrada final. |

Os notebooks 06–09b dependem dos produtos da camada Consumo e podem ser executados de acordo com a investigação desejada.

A auditoria integrada pode ser executada após a geração das camadas Gold, Analytic e Consumo.

## 7. Rastreabilidade e validação

A rastreabilidade dos produtos é realizada por meio de manifestos e catálogos associados às camadas de processamento.

Entre os principais controles implementados estão:

- Verificação da existência dos arquivos de origem;
- Validação dos esquemas e das contagens de registros;
- Verificação da integridade dos arquivos Parquet;
- Conferência das referências territoriais;
- Validação das chaves dos produtos analíticos;
- Verificação de duplicidades;
- Conferência da cobertura temporal e municipal;
- Registro dos resultados das auditorias.

Esses mecanismos permitem acompanhar a execução, identificar falhas e verificar a consistência dos produtos disponibilizados para análise.

## 8. Considerações finais

O conjunto de notebooks apresentado nesta pasta representa o fluxo operacional e analítico do Projeto ENEM.

A arquitetura permite organizar os microdados históricos, padronizar diferentes estruturas de dados, produzir indicadores agregados e desenvolver investigações sobre a participação e o desempenho dos participantes do exame.

A separação entre processamento, construção de produtos analíticos, consumo e investigação estatística favorece a rastreabilidade, a manutenção e a ampliação do projeto para diferentes unidades federativas e períodos históricos.