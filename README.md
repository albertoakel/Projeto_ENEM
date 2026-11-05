# Projeto ENEM — Engenharia, análise temporal e espacial dos microdados (1998–2025)

## Visão geral

Este projeto organiza os microdados históricos do Exame Nacional do Ensino Médio (ENEM), de 1998 a 2025, em uma estrutura padronizada e orientada à análise municipal.

A primeira fase utiliza a arquitetura Medalhão para transformar as fontes originais em produtos analíticos rastreáveis:

**Bronze → Silver → Gold → Analytic → Consumo**

O processamento é realizado por Unidade da Federação (UF), respeitando as diferenças de estrutura dos microdados ao longo dos anos.

O projeto também inclui notebooks de análise exploratória transversal, longitudinal e espacial.

## Objetivos

- Organizar os microdados históricos do ENEM.
- Reduzir o volume de dados por meio da seleção de variáveis relevantes.
- Harmonizar schemas e referências territoriais.
- Construir indicadores municipais de participação, perfil e desempenho.
- Investigar padrões temporais e espaciais.
- Preparar bases para dashboard e modelos estatísticos/Machine Learning.

## Arquitetura de dados

| Camada | Responsabilidade |
|---|---|
| **Bronze** | Inventário e preservação dos ZIPs originais |
| **Staging** | Extração temporária dos CSVs |
| **Silver** | Seleção de variáveis, filtro por UF e conversão para Parquet |
| **Gold** | Schema canônico de 29 colunas e harmonização territorial, preservando registros individuais |
| **Analytic** | Oito produtos agregados por município, ano e grupos |
| **Consumo** | Painel municipal integrado e produtos auxiliares prontos para análise |

A Gold preserva o nível dos registros. As agregações estatísticas são realizadas somente na Analytic. A construção da Gold está implementada diretamente em `executar_pipeline.py`; Silver, Analytic e Consumo utilizam seus módulos próprios.

### Referência territorial

A referência territorial utilizada muda historicamente:

| Período | Referência |
|---|---|
| 1998–2000 | Município de residência |
| 2001–2007 | Município da escola |
| 2008–2025 | Município da prova |

A coluna `TIPO_REFERENCIA_TERRITORIAL` registra essa diferença e deve ser considerada nas análises temporais.

### Particularidade de 2024 e 2025

A partir de 2024, o processamento utiliza duas fontes:

- `PARTICIPANTES`: demografia e faixa etária.
- `RESULTADOS`: presença, notas, escola e grupos analíticos.

Não é realizado join individual entre essas fontes. A compatibilidade é tratada no nível municipal.

## Execução do pipeline

O processamento completo é orquestrado por `executar_pipeline.py`. Ao iniciar, o programa solicita a UF, o ano inicial e o ano final no terminal (com padrões 1998 e 2025).

```bash
python executar_pipeline.py
```

Antes da execução:

1. Disponibilize os ZIPs originais em `data/bronze/`.
2. Verifique a UF definida no bloco principal de `executar_pipeline.py`.
3. Confirme o intervalo de anos.
4. Verifique o catálogo `data/metadata/dicionarios/variaveis_enem_por_ano.csv`.
5. Configure o ambiente e as dependências Python.

O pipeline não realiza o download automático dos ZIPs. A extração e o processamento são realizados ano a ano, evitando acumular todos os CSVs no Staging.

**Configuração:** a UF é informada pelo usuário no terminal. `src/enem_pipeline/config.py` mantém PA como UF padrão para chamadas às funções sem UF explícita; o orquestrador passa a UF informada pelo usuário.

## Estrutura dos diretórios de dados

```text
data/
├── bronze/       # ZIPs originais
├── staging/      # CSVs temporários
├── silver/       # Parquets filtrados por UF e ano
├── gold/         # Registros com schema canônico
├── analytic/     # Produtos estatísticos municipais
├── consumo/      # Painel e produtos para análise
└── metadata/
    └── dicionarios/
        └── variaveis_enem_por_ano.csv
```

Os produtos processados são organizados por UF. As camadas Silver e Gold também são particionadas por ano e, na Gold, por base de origem.

## Produtos da camada Analytic

1. `demografia_municipal`
2. `faixa_etaria_municipal`
3. `presenca_municipal`
4. `desempenho_redacao_municipal`
5. `desempenho_objetiva_municipal`
6. `desempenho_areas_municipal`
7. `escola_municipal`
8. `desempenho_grupos_municipal`

## Produtos da camada Consumo

- `painel_municipal`
- `faixa_etaria_municipal`
- `desempenho_grupos_municipal`

O painel integra indicadores por ano e município. Os produtos de faixa etária e grupos são mantidos separadamente por possuírem granularidade própria.

## Notebooks

| Notebook | Conteúdo |
|---|---|
| `00_Download_data_ENEM.ipynb` | Obtenção das fontes |
| `01_Verificar_configuracao.ipynb` | Verificações iniciais |
| `02_Execucao_silver_todos_anos_por_uf.ipynb` | Execução Silver |
| `02a_Auditoria_silver.ipynb` | Auditoria Silver |
| `03_Execucao_gold_municipio_ano.ipynb` | Execução Gold |
| `03a_Auditoria_gold.ipynb` | Auditoria Gold |
| `04_Execucao_analitico.ipynb` | Execução Analytic |
| `05_Execucao_consumo.ipynb` | Execução Consumo |
| `06_Analise_transversal.ipynb` | EDA transversal |
| `07_Analise_transversal_mapas.ipynb` | Mapas transversais |
| `08_Analise_longitudinal.ipynb` | EDA longitudinal |
| `09a_Analise_longitudinal_mapas.ipynb` | Mapas longitudinais |
| `09b_Analise_longitudinal_mapas_folium.ipynb` | Mapas interativos |

## Periodização das análises de desempenho

| Período | Estrutura |
|---|---|
| 1998–2008 | OBJETIVA e REDAÇÃO |
| 2009–2025 | CN, CH, LC, MT e REDAÇÃO |

Os períodos não devem ser tratados automaticamente como uma série homogênea. As diferenças de estrutura e critérios precisam ser consideradas na interpretação.

## Fases do projeto

### Fase 1 — Engenharia e análise exploratória

Organização dos dados com arquitetura Medalhão, construção de produtos municipais e realização de EDA transversal, longitudinal e espacial.

### Fase 2 — Dashboard

Construção de uma interface de visualização, com tecnologia ainda a definir. A camada Consumo será a principal fonte de dados para essa etapa.

### Fase 3 — Modelagem e investigação

Aplicação de métodos estatísticos e Machine Learning para investigar padrões espaciais, tendências temporais, relações entre indicadores e agrupamentos de municípios.

## Documentação técnica

Consulte **[DOCUMENTACAO.md](docs/DOCUMENTACAO.md)** para conhecer em detalhe:

- o fluxo operacional;
- as transformações entre camadas;
- o contrato canônico da Gold;
- as variáveis e métricas da Analytic;
- a integração da Consumo;
- as regras de comparabilidade histórica;
- as auditorias e os manifestos.

## Tecnologias principais

- Python
- DuckDB
- Pandas
- Parquet
- Jupyter Notebook
- GeoPandas e Folium para análises espaciais



## Observação sobre o orquestrador

Na versão `executar_pipeline(1).py` recebida para correção, o bloco `if __name__ == "__main__"` chama `main()` duas vezes. Antes de executar, mantenha somente `raise SystemExit(main())` nesse bloco, para evitar iniciar o pipeline interativo em duplicidade.
