# Projeto ENEM — Análise histórica, territorial e educacional

> **Documento:** documentação geral do projeto  
> **Período dos microdados:** 1998–2025  
> **Organização territorial:** Unidades da Federação e municípios  
> **Documento complementar:** [`DOCUMENTACAO_MEDALHAO.md`](DOCUMENTACAO_MEDALHAO.md)

---

## 1. Apresentação

O Projeto ENEM reúne rotinas de engenharia e análise de dados voltadas à organização, padronização e exploração histórica dos microdados do Exame Nacional do Ensino Médio (ENEM).

O projeto parte dos arquivos oficiais de diferentes edições do exame e constrói bases organizadas em camadas, com padronização de variáveis e referências territoriais. A partir dessas bases, são produzidos conjuntos de dados agregados por município e ano, utilizados em análises transversais, espaciais e longitudinais e em um dashboard interativo.

A série histórica considerada nesta versão compreende as edições de **1998 a 2025**. A estrutura de processamento permite selecionar uma Unidade da Federação (UF) e um intervalo de anos, desde que as fontes correspondentes estejam disponíveis na camada de dados de origem.

O projeto utiliza principalmente Python, DuckDB, Pandas e arquivos Parquet. As análises e visualizações são desenvolvidas em notebooks e em uma aplicação web baseada em Dash.

## 2. Objetivos

### 2.1 Objetivo geral

Construir uma estrutura reprodutível para organizar e analisar os microdados históricos do ENEM, permitindo investigar a participação, o desempenho e características dos participantes em diferentes escalas temporais e territoriais.

### 2.2 Objetivos específicos

- Organizar os arquivos de microdados de diferentes edições do ENEM em uma estrutura de dados consistente.
- Selecionar e processar os registros de uma UF, reduzindo o volume de dados necessário às análises.
- Harmonizar variáveis e estruturas que mudaram ao longo da série histórica.
- Construir uma representação territorial padronizada para as diferentes referências disponíveis nos microdados.
- Produzir indicadores e estatísticas agregados por município e ano.
- Permitir análises transversais, espaciais e longitudinais.
- Disponibilizar os resultados por meio de um dashboard interativo.
- Manter registros de processamento, manifestos e auditorias que apoiem a rastreabilidade dos produtos.

## 3. Escopo e unidade de análise

### 3.1 Escopo temporal

O escopo histórico desta versão vai de **1998 a 2025**, totalizando 28 edições do exame.

A disponibilidade de variáveis não é uniforme ao longo desse período. A estrutura dos microdados, os nomes das colunas, os campos territoriais e a organização dos arquivos de origem sofreram alterações. Por isso, a série não deve ser interpretada como uma base originalmente homogênea: a comparabilidade depende das regras de seleção, harmonização e agregação implementadas no projeto.

### 3.2 Escopo geográfico

O processamento é organizado por Unidade da Federação. A estrutura observada no repositório contempla diretórios de dados para as 27 UFs brasileiras.

A seleção de uma UF é feita a partir de uma variável territorial disponível na edição correspondente. A interpretação dessa seleção precisa considerar a referência utilizada em cada período, descrita na Seção 5.

### 3.3 Unidade de análise

Os produtos analíticos deste projeto são predominantemente agregados por:

- ano do exame;
- código e nome do município;
- tipo de referência territorial;
- grupos de participantes, quando as variáveis necessárias estão disponíveis;
- área de conhecimento ou componente avaliado, quando aplicável.

Os resultados municipais representam estatísticas agregadas dos registros disponíveis. Não devem ser interpretados como microdados individuais nem como medidas diretas de características de cada escola ou de cada participante.

### 3.4 Variáveis e questionários

O processamento prioriza variáveis relacionadas à identificação temporal, características dos participantes, presença, notas, redação, escola e localização territorial.

O projeto não tem como objetivo, nesta configuração, processar integralmente o questionário socioeconômico. A seleção de variáveis é orientada pelas questões analíticas contempladas nos produtos atualmente implementados.

## 4. Fontes de dados e características históricas

A fonte principal são os microdados oficiais do ENEM, organizados por edição e armazenados inicialmente em arquivos compactados na camada Bronze.

A organização dos arquivos de origem não é idêntica em todos os anos. De forma geral:

- nas edições até 2023, o processamento utiliza o arquivo principal de microdados da respectiva edição;
- nas edições de 2024 e 2025, os dados estão distribuídos em arquivos distintos, incluindo bases de participantes e de resultados.

Essa separação recente tem consequências para a integração das informações: os arquivos de participantes e resultados são tratados como bases de origem distintas. Não se pressupõe uma correspondência individual entre os registros dessas bases quando não há uma chave de relacionamento validada para essa finalidade.

O projeto mantém um catálogo histórico de variáveis por edição em:

```text
data/metadata/dicionarios/variaveis_enem_por_ano.csv
```

O inventário documentado durante o desenvolvimento identificou 71 variáveis distintas ao longo da série e 11 variáveis presentes em todas as edições analisadas:

- `NU_ANO`
- `NU_INSCRICAO`
- `NU_NOTA_REDACAO`
- `NU_NOTA_COMP1`
- `NU_NOTA_COMP2`
- `NU_NOTA_COMP3`
- `NU_NOTA_COMP4`
- `NU_NOTA_COMP5`
- `TP_STATUS_REDACAO`
- `TP_FAIXA_ETARIA`
- `TP_SEXO`

A presença de uma variável em todos os anos não significa, por si só, que sua semântica, preenchimento ou distribuição sejam invariáveis. Essas características devem ser consideradas nas análises.

## 5. Referências territoriais e comparabilidade

A dimensão territorial é central para a organização dos dados e para a interpretação dos resultados municipais. Entretanto, a referência geográfica disponível nos microdados varia ao longo da série.

| Período | Referência territorial utilizada |
|---|---|
| 1998–2000 | Município de residência |
| 2001–2007 | Município da escola |
| 2008–2023 | Município da escola e município de prova |
| 2024–2025 — participantes | Município de prova |
| 2024–2025 — resultados | Município da escola e município de prova |

As referências são identificadas como:

- `RESIDENCIA`: município de residência;
- `ESC`: município da escola;
- `PROVA`: município de aplicação da prova.

A padronização permite armazenar diferentes perspectivas territoriais em uma estrutura comum, mas não torna essas perspectivas equivalentes.

**Uma série por município de residência não é diretamente intercambiável com uma série por município da escola ou de prova.** Comparações temporais devem explicitar a referência utilizada e respeitar as mudanças de cobertura.

Há ainda uma particularidade importante no processamento por UF: a seleção dos registros na camada Silver, a partir de 2008, utiliza a UF do local de prova. Na geração de registros com referência `ESC`, a perspectiva escolar é construída a partir desses registros selecionados, sem uma nova seleção pela UF da escola. Portanto, o identificador `uf=UF` no caminho dos produtos representa a UF utilizada na seleção de origem, e não garante que toda referência escolar associada pertença à mesma UF.

No dashboard, a referência `RESIDENCIA` é apresentada sob a opção `ESC` para compatibilização da interface. Essa convenção de visualização não altera a natureza original da referência e deve ser considerada ao interpretar os primeiros anos da série.

## 6. Organização geral do repositório

A estrutura do projeto separa os dados processados, o código-fonte, os notebooks e a aplicação de visualização.

```text
Projeto_ENEM/
├── data/
│   ├── bronze/
│   ├── staging/
│   ├── silver/
│   ├── gold/
│   ├── analytic/
│   ├── consumo/
│   ├── metadata/
│   │   └── dicionarios/
│   ├── reports/
│   └── shapefiles/
├── dash/
│   ├── app.py
│   ├── assets/
│   ├── components/
│   ├── dash_utils/
│   └── pages/
├── docs/
│   ├── DOCUMENTACAO_PROJETO.md
│   └── DOCUMENTACAO_MEDALHAO.md
├── notebook/
├── src/
│   ├── enem_pipeline/
│   └── utils/
├── executar_pipeline.py
├── executar_pipeline_lista.py
└── README.md
```

A árvore acima apresenta os diretórios e componentes principais, não todos os arquivos e partições de dados.

### 6.1 Diretório `data/`

Armazena os dados de origem, intermediários e produtos processados. As camadas seguem a arquitetura Bronze, Staging, Silver, Gold, Analytic e Consumo. Também são mantidos metadados, relatórios e arquivos geográficos utilizados nas análises.

Os produtos são organizados por UF e, quando aplicável, por ano, base de origem ou referência territorial. Os dados tabulares processados são gravados predominantemente em formato Parquet com compressão Zstandard.

### 6.2 Diretório `src/`

Contém os módulos reutilizáveis do projeto.

O pacote `src/enem_pipeline/` reúne os módulos responsáveis pelo processamento e pela construção das camadas de dados, incluindo configuração, inventário, catálogo, processamento Silver, padronização Gold, geração Analytic e integração Consumo.

O pacote `src/utils/` reúne funções auxiliares utilizadas em tarefas de análise e preparação dos dados.

### 6.3 Diretório `notebook/`

Reúne notebooks de processamento, análise e investigação, organizados em dois diretórios com responsabilidades distintas:

- `pipeline/`: notebooks de obtenção, configuração, processamento das camadas, análises transversais e longitudinais e auditoria integrada;
- `estudos_analiticos/`: notebooks das oito questões de pesquisa (Q1–Q8), desenvolvidas a partir dos produtos disponibilizados pelo pipeline.

O diretório `pipeline/` inclui, entre outros, os notebooks `00_Download_data_ENEM.ipynb`, `01_Verificar_configuracao.ipynb`, `02_Execucao_Silver.ipynb`, `03_Execucao_Gold.ipynb`, `04_Execucao_Analitico.ipynb`, `05_Execucao_Consumo.ipynb`, `06_Analise_transversal.ipynb`, `07_Analise_transversal_mapas.ipynb`, `08_Analise_longitudinal.ipynb`, `09a_Analise_longitudinal_mapas.ipynb`, `09b_Analise_longitudinal_mapas_folium.ipynb` e `10_auditoria_integrada_final.ipynb`.

O diretório `estudos_analiticos/` contém os estudos Q1–Q7 e dois notebooks complementares para o Q8: `Q8A_CLUSTERINGS_METODO.ipynb` e `Q8B_CLUSTERINGS_APLICACAO.ipynb`.

Os notebooks de execução acompanham as etapas de preparação e transformação dos dados. Os notebooks analíticos exploram os produtos gerados, enquanto os notebooks de auditoria verificam aspectos de integridade e consistência. A descrição individual dos estudos está disponível em `notebook/estudos_analiticos/README.md`.

### 6.4 Diretório `dash/`

Contém a aplicação interativa baseada em Dash, seus módulos de páginas, utilitários de carregamento e desempenho, componentes e recursos estáticos.

### 6.5 Diretório `docs/`

Concentra a documentação do projeto. Nesta etapa, são mantidos dois documentos:

- `DOCUMENTACAO_PROJETO.md`: visão geral, escopo, dados, análises e dashboard;
- `DOCUMENTACAO_MEDALHAO.md`: descrição técnica da arquitetura de dados e das etapas do pipeline.

## 7. Fluxo geral de dados e produtos

```text
Microdados oficiais do ENEM
            │
            ▼
     Bronze / Staging
            │
            ▼
          Silver
            │
            ▼
           Gold
            │
            ▼
         Analytic
            │
            ▼
          Consumo
            │
       ┌────┴────┐
       ▼         ▼
   Notebooks  Dashboard
   analíticos  Dash
```

A arquitetura detalhada, as regras de transformação, os manifestos e os procedimentos de validação de cada camada estão descritos em [`DOCUMENTACAO_MEDALHAO.md`](DOCUMENTACAO_MEDALHAO.md).

Em termos gerais:

- **Bronze e Staging** organizam os arquivos de origem e a extração temporária necessária ao processamento.
- **Silver** seleciona os registros da UF e as variáveis de interesse.
- **Gold** harmoniza o esquema e as dimensões territoriais em uma estrutura canônica.
- **Analytic** produz estatísticas e agregações municipais destinadas à investigação.
- **Consumo** integra produtos analíticos e organiza bases adequadas às aplicações de visualização.

O processamento pode ser executado por meio dos notebooks ou dos scripts de orquestração disponíveis na raiz do projeto. O orquestrador `executar_pipeline.py` solicita a UF e os anos inicial e final, verifica a disponibilidade dos arquivos de origem e executa as etapas do pipeline.

O script não realiza o download automático dos microdados: os arquivos compactados correspondentes ao período solicitado devem estar previamente disponíveis em `data/bronze/`.

## 8. Produtos analíticos

A camada Analytic produz agregações municipais a partir dos dados padronizados na camada Gold. Na implementação documentada, são construídos nove produtos:

| Produto | Finalidade geral |
|---|---|
| `demografia_municipal` | Caracterização agregada dos participantes por município e ano |
| `faixa_etaria_municipal` | Distribuição dos participantes por grupos de faixa etária |
| `presenca_municipal` | Indicadores relacionados à presença no exame |
| `desempenho_redacao_municipal` | Estatísticas municipais das notas de redação |
| `desempenho_objetiva_municipal` | Estatísticas da nota objetiva, quando aplicável |
| `desempenho_areas_municipal` | Estatísticas das notas por área do conhecimento |
| `escola_municipal` | Agregações relacionadas às características da escola |
| `desempenho_grupos_municipal` | Estatísticas de desempenho por grupos de participantes |
| `desempenho_sexo_faixa_etaria_municipal` | Estatísticas de desempenho por sexo e faixa etária |

As estatísticas de desempenho implementadas incluem, conforme o produto e a variável, contagem de registros, quantidade de valores válidos, quantidade de notas iguais a zero, média, média de valores positivos, mediana, desvio-padrão e quartis.

A disponibilidade e a interpretação de cada produto dependem das variáveis existentes na edição e das regras de processamento. A existência de um arquivo de produto não significa necessariamente que ele contenha registros para todos os anos ou todas as referências territoriais.

### 8.1 Mudanças na estrutura das notas

A representação das notas objetivas mudou ao longo da série. Até 2008, o projeto considera a variável `NU_NOTA_OBJETIVA`. A partir de 2009, o desempenho objetivo é representado pelas notas das quatro áreas:

- Ciências da Natureza (CN);
- Ciências Humanas (CH);
- Linguagens e Códigos (LC);
- Matemática (MT).

A nota de redação é tratada separadamente. Por isso, uma comparação histórica deve considerar a mudança na estrutura de avaliação e não presumir que a variável objetiva tenha o mesmo significado em todos os anos.

## 9. Produtos da camada Consumo

A camada Consumo organiza os produtos analíticos para facilitar sua utilização nas análises e no dashboard. Na implementação atual, são produzidos quatro conjuntos:

| Produto | Conteúdo geral |
|---|---|
| `painel_municipal` | Integração de indicadores demográficos, presença, redação, desempenho objetivo, áreas e escola |
| `faixa_etaria_municipal` | Distribuição municipal por grupos de faixa etária |
| `desempenho_grupos_municipal` | Desempenho agregado por grupos |
| `desempenho_sexo_faixa_etaria_municipal` | Desempenho agregado por sexo e faixa etária |

O painel municipal integra produtos por ano, código municipal e referência territorial. A integração utiliza junções externas para preservar municípios presentes em apenas uma das bases de origem.

Os demais produtos permanecem separados porque possuem granularidades diferentes e não devem ser incorporados ao painel municipal sem considerar suas chaves e dimensões específicas.

### 9.1 Limitação das edições de 2024 e 2025

Nas edições de 2024 e 2025, as informações demográficas e de faixa etária são provenientes da base de participantes, enquanto informações de presença, redação, áreas e escola são provenientes da base de resultados.

Como o projeto não estabelece um relacionamento individual validado entre essas duas bases, não se deve interpretar os produtos como se permitissem cruzar diretamente sexo ou faixa etária com notas individuais nessas edições. Em particular, o produto de desempenho por sexo e faixa etária pode não apresentar registros para 2024 e 2025.

Essa limitação decorre da organização das fontes disponíveis e deve ser considerada na leitura dos resultados e na interpretação das auditorias.

## 10. Análises desenvolvidas

Os notebooks analíticos exploram os produtos gerados nas camadas Analytic e Consumo. As frentes identificadas na estrutura atual são descritas a seguir.

### 10.1 Análise transversal

Investiga diferenças entre municípios em um mesmo ano ou em períodos selecionados. Pode envolver a distribuição dos indicadores, comparações entre grupos e identificação de padrões espaciais.

### 10.2 Análise espacial

Utiliza os códigos municipais e os arquivos geográficos armazenados em `data/shapefiles/` para representar indicadores em mapas. A análise espacial permite observar a distribuição territorial dos resultados e comparar padrões entre municípios.

A correspondência entre tabelas e geometrias é realizada por identificadores municipais, com tratamento dos nomes para apoiar a consistência da apresentação.

### 10.3 Análise longitudinal

Investiga a evolução dos indicadores ao longo das edições do ENEM. A leitura longitudinal deve considerar as mudanças históricas nas variáveis, nas bases de origem e nas referências territoriais descritas neste documento.

### 10.4 Análises longitudinais com mapas

Os notebooks específicos de mapas longitudinais permitem explorar a distribuição espacial dos indicadores ao longo do tempo. A interpretação dessas visualizações depende da disponibilidade dos dados para cada edição e da compatibilidade da referência territorial selecionada.

### 10.5 Estudos analíticos organizados por questões de pesquisa

Além das análises gerais realizadas nos notebooks do pipeline, o projeto reúne oito estudos analíticos independentes, organizados por questões de pesquisa e desenvolvidos a partir dos produtos da camada Consumo.

| Eixo | Tema investigado |
|---|---|
| Q1 | Evolução da participação no ENEM |
| Q2 | Desigualdade de gênero |
| Q3 | Desempenho por dependência administrativa da escola |
| Q4 | Idade e trajetória dos participantes |
| Q5 | Desigualdade territorial e desempenho municipal |
| Q6 | Distribuição e desigualdade do desempenho |
| Q7 | Relações entre participação, perfil e desempenho |
| Q8 | Perfis multidimensionais de desempenho municipal |

Os estudos Q1–Q7 investigam, sob diferentes perspectivas, a evolução da participação, a composição dos participantes, as diferenças entre grupos e redes de ensino, a distribuição das notas e as desigualdades territoriais. Empregam indicadores descritivos, comparações temporais, medidas de concentração e dispersão, correlações e análises de tendências, conforme a questão de pesquisa.

O eixo Q8 amplia esse conjunto ao investigar a formação de perfis municipais considerando simultaneamente as cinco disciplinas do ENEM a partir de 2009. Ele é dividido em dois notebooks complementares.

#### Q8A — Método e seleção do algoritmo

O Q8A investiga estratégias de clusterização para identificar municípios com padrões semelhantes de desempenho multidisciplinar. A unidade de análise é o município por edição, considerando uma coorte balanceada de 37 municípios com dados completos nas 15 edições de 2009 a 2023, totalizando 555 observações município-ano.

As cinco variáveis utilizadas são Ciências Humanas (CH), Ciências da Natureza (CN), Linguagens e Códigos (LC), Matemática (MT) e Redação. A padronização é realizada separadamente em cada edição, preservando a comparação relativa entre municípios dentro do mesmo ano.

A avaliação metodológica compara K-Means, agrupamento aglomerativo pelo método Ward, Gaussian Mixture Model (GMM) e DBSCAN. São consideradas métricas de qualidade de agrupamento, como Silhouette, Calinski–Harabasz e Davies–Bouldin, além de critérios específicos de cada algoritmo quando aplicáveis. Também são avaliados o número e o tamanho dos grupos e a estabilidade das partições diante de perturbações gaussianas, por meio do Adjusted Rand Index (ARI).

O método selecionado para a aplicação é o **K-Means com K=2**. A escolha não decorre de superioridade em todas as métricas de separação: considera conjuntamente a qualidade das partições, a estabilidade média diante das perturbações, o equilíbrio dos grupos e a interpretabilidade de uma solução com dois perfis. Na comparação controlada para K=2, Ward apresentou Silhouette mediana de 0,4673 e K-Means de 0,4606; por outro lado, o K-Means apresentou ARI médio superior ao Ward nas nove combinações de número de grupos e intensidade de perturbação avaliadas.

#### Q8B — Aplicação e caracterização dos perfis municipais

O Q8B aplica o método selecionado no Q8A à mesma coorte de 37 municípios e às 15 edições de 2009 a 2023. O K-Means é ajustado de forma independente em cada edição, sempre com K=2, após a padronização anual das cinco disciplinas. A aplicação utiliza também um critério de elegibilidade de mais de 100 participantes.

Como os rótulos originais do K-Means não possuem significado ordinal, os grupos são ordenados anualmente pela média dos escores padronizados das cinco disciplinas:

- **Perfil A:** maior desempenho multidisciplinar relativo dentro da edição;
- **Perfil B:** menor desempenho multidisciplinar relativo dentro da edição.

A análise caracteriza a qualidade da separação, a distribuição e o tamanho dos grupos, os escores padronizados, as médias das disciplinas em pontos do ENEM, a evolução temporal, a distribuição espacial e as transições de classificação entre 2009 e 2023.

Entre os principais resultados documentados estão:

- A Silhouette apresentou média de 0,4533 e mediana de 0,4606 nas 15 edições, variando de 0,3889 em 2013 a 0,5116 em 2021.
- O Perfil A apresentou médias superiores ao Perfil B nas cinco disciplinas em todas as 15 edições.
- A maior diferença média entre os perfis ocorreu em Redação (49,58 pontos), seguida por Matemática (26,56), Linguagens (25,14), Ciências Humanas (24,66) e Ciências da Natureza (21,11).
- Embora a coorte permaneça fixa em 37 municípios, a composição de cada perfil varia entre as edições.
- Entre 2009 e 2023, 32 municípios (86,5%) permaneceram no mesmo perfil e cinco (13,5%) mudaram de classificação. Quatro passaram do Perfil A para o Perfil B; Redenção passou do Perfil B para o Perfil A.

**Limites de interpretação do Q8:** os perfis representam posições relativas dentro de cada edição, pois o modelo é reajustado anualmente. Assim, a mudança de perfil de um município não demonstra, isoladamente, melhora ou piora absoluta do desempenho. Da mesma forma, as médias anuais de cada perfil combinam variações nas notas e mudanças na composição dos grupos; não representam a trajetória de conjuntos fixos de municípios.

A documentação detalhada dos procedimentos e resultados de cada eixo está disponível em `notebook/estudos_analiticos/README.md`.

## 11. Dashboard interativo

O projeto possui uma aplicação web desenvolvida com **Dash**, utilizando componentes de visualização do ecossistema Plotly e recursos geográficos para a representação municipal.

O dashboard consome os arquivos da camada Consumo e os shapefiles municipais. Sua estrutura atual está organizada em quatro páginas.

### 11.1 Visão Geral

Apresenta uma visão consolidada da série histórica, com indicadores de participação e desempenho e comparações agregadas. As médias estaduais exibidas para notas são calculadas de forma ponderada pela quantidade de valores válidos, conforme a implementação da aplicação.

### 11.2 Mapas Municipais

Apresenta mapas temáticos e recursos de comparação entre municípios, incluindo representações por indicadores, rankings e distribuições.

A cobertura de cada indicador depende da disponibilidade histórica correspondente. A nota objetiva, por exemplo, não possui a mesma representação antes e depois da mudança ocorrida em 2009.

### 11.3 Análise Municipal

Permite acompanhar a evolução de um município e compará-lo com outros municípios selecionados. A página contempla visualizações de tendências, dispersão, correlação e comparações relacionadas à rede de ensino.

Algumas visualizações aplicam critérios mínimos de quantidade de registros válidos para destacar pontos ou grupos. Esses critérios devem ser considerados na interpretação dos gráficos.

### 11.4 Perfil dos Participantes

Apresenta informações agregadas sobre sexo e faixa etária, incluindo distribuições e comparações disponíveis na série.

Os códigos de `TP_FAIXA_ETARIA` são categorias codificadas, e não valores de idade em anos. Para fins de apresentação, o dashboard agrupa esses códigos em categorias mais amplas. As análises que relacionam perfil e desempenho também dependem da disponibilidade de cruzamentos válidos entre as bases de origem.

### 11.5 Filtros e referências

A interface possui seleção de UF e referência territorial. A UF padrão configurada na aplicação é PA. As referências disponíveis na interface são `ESC` e `PROVA`.

A visualização `ESC` utiliza a convenção descrita na Seção 5 para os anos em que a referência histórica disponível é `RESIDENCIA`. Além disso, os mapas são apresentados sobre a geometria da UF selecionada; portanto, registros associados a municípios fora dessa geometria não são exibidos como municípios pertencentes à UF selecionada.

### 11.6 Carregamento e desempenho

A aplicação utiliza mecanismos de cache para reduzir leituras repetidas dos arquivos Parquet e dos shapefiles, além de reutilizar layouts de páginas já construídos. Há instrumentação de logs para acompanhar tempos de execução, callbacks e ocorrências de cache.

Esses mecanismos melhoram a experiência de navegação, mas não eliminam o custo de leitura e preparação inicial dos dados de uma UF. O tempo de carregamento pode variar conforme o volume de registros, o tamanho das geometrias e os recursos disponíveis na máquina.

A aplicação está configurada no código atual para execução local em `127.0.0.1`, na porta `8050`, com modo de depuração habilitado. Essa configuração deve ser revista antes de qualquer implantação em ambiente de produção.

## 12. Tecnologias utilizadas

| Tecnologia | Utilização no projeto |
|---|---|
| Python | Linguagem principal |
| DuckDB | Consulta e processamento de dados tabulares |
| Pandas | Manipulação e agregação de dados |
| Parquet | Armazenamento colunar dos dados processados |
| Zstandard (ZSTD) | Compressão dos arquivos Parquet |
| Jupyter Notebook | Execução de etapas e análises exploratórias |
| Dash | Aplicação web interativa |
| Plotly | Gráficos e visualizações |
| Folium | Recursos de visualização geográfica em notebooks |
| Shapefiles | Geometrias municipais utilizadas nos mapas |

A configuração do ambiente e as dependências devem ser mantidas de acordo com os arquivos e instruções operacionais presentes no repositório. Esta documentação não fixa versões de todos os pacotes, pois elas podem mudar entre ambientes e atualizações do projeto.

## 13. Validação, rastreabilidade e qualidade

O projeto inclui procedimentos de validação em diferentes etapas do processamento. Entre os mecanismos implementados estão:

- verificação da disponibilidade dos arquivos de origem;
- validação dos arquivos extraídos;
- verificação de leitura e consistência dos Parquets;
- conferência de UF e ano nos registros processados;
- padronização e validação do esquema Gold;
- geração de catálogos e manifestos;
- validação de chaves e dimensões nas agregações;
- verificação dos produtos gerados na camada Consumo;
- auditorias integradas dos produtos e arquivos.

Os manifestos e relatórios são armazenados na área de metadados e relatórios do projeto. Eles apoiam a identificação dos arquivos utilizados e produzidos, bem como a verificação do estado de execução.

Uma auditoria aprovada indica que os critérios implementados foram atendidos. Isso não equivale, por si só, a uma validação científica de todas as hipóteses ou interpretações que possam ser construídas a partir dos dados.

## 14. Limitações e cuidados de interpretação

As principais limitações conhecidas para a interpretação dos resultados são:

1. **Mudanças históricas nos microdados:** nomes, disponibilidade e estrutura das variáveis variam entre as edições.
2. **Mudanças de referência territorial:** residência, escola e prova são perspectivas diferentes e não devem ser tratadas como uma única série sem ressalvas.
3. **Bases separadas em 2024 e 2025:** não há cruzamento individual validado entre participantes e resultados na implementação descrita.
4. **Disponibilidade desigual dos produtos:** um produto pode não possuir registros para todos os anos, municípios ou referências.
5. **Agregação municipal:** estatísticas municipais não descrevem a distribuição individual completa dos participantes.
6. **Mudanças na avaliação:** a estrutura das notas objetivas mudou ao longo da série, exigindo cautela em comparações históricas.
7. **Cobertura geográfica dos mapas:** a exibição depende dos municípios presentes na geometria da UF selecionada e da referência territorial utilizada.
8. **Interpretação estatística:** médias, dispersões, correlações e indicadores agregados não demonstram, isoladamente, relações causais.
9. **Perfis municipais do Q8:** os agrupamentos são estimados separadamente por edição e expressam posições relativas entre municípios elegíveis; as transições não devem ser interpretadas como variações absolutas de desempenho.

As análises devem explicitar o período, a UF, a referência territorial, a variável e a população de registros considerados. Sempre que uma comparação atravessar mudanças estruturais importantes, essas mudanças devem ser descritas junto aos resultados.

## 15. Como executar o projeto

### 15.1 Pré-requisitos gerais

Para executar o projeto, é necessário dispor de:

- ambiente Python com as dependências utilizadas pelo projeto;
- arquivos compactados dos microdados correspondentes aos anos desejados em `data/bronze/`;
- estrutura de diretórios configurada;
- arquivos geográficos municipais necessários para as análises espaciais e para o dashboard.

### 15.2 Execução do pipeline

Na raiz do projeto, execute:

```bash
python executar_pipeline.py
```

O script solicita a sigla da UF, o ano inicial e o ano final. O intervalo informado deve estar compreendido entre 1998 e 2025, e o ano inicial não pode ser posterior ao ano final. O processamento depende da presença dos arquivos de origem para todos os anos solicitados.

Também existe o script `executar_pipeline_lista.py`, destinado à execução em lote conforme sua configuração.

O orquestrador não realiza o download automático dos microdados: os arquivos compactados correspondentes ao período solicitado devem estar previamente disponíveis em `data/bronze/`.

### 15.3 Execução do dashboard

A partir do diretório `dash/`, execute:

```bash
python app.py
```

Na configuração local atual, a aplicação é disponibilizada em:

```text
http://127.0.0.1:8050
```

O dashboard depende dos produtos da camada Consumo e dos shapefiles necessários à UF selecionada.

### 15.4 Notebooks

Os notebooks do diretório `notebook/` podem ser utilizados para executar etapas específicas, realizar análises ou executar auditorias. Recomenda-se respeitar a ordem lógica das dependências: os produtos analíticos e o dashboard dependem das camadas processadas anteriormente.

Para detalhes de cada etapa do pipeline, consulte [`DOCUMENTACAO_MEDALHAO.md`](DOCUMENTACAO_MEDALHAO.md).

## 16. Organização da documentação

A documentação do repositório está concentrada diretamente no diretório `docs/`, sem subdivisão em pastas.

| Documento | Responsabilidade |
|---|---|
| `DOCUMENTACAO_PROJETO.md` | Visão geral, objetivos, fontes, organização, análises, dashboard e limitações |
| `DOCUMENTACAO_MEDALHAO.md` | Detalhamento técnico da arquitetura de dados, transformações, regras e validações do pipeline |

O `README.md`, na raiz do repositório, deve funcionar como porta de entrada: apresentar brevemente o projeto e direcionar o leitor para a documentação e para as instruções de execução.

## 17. Manutenção deste documento

Esta documentação descreve a estrutura e as funcionalidades identificadas na versão do repositório analisada durante sua elaboração. Como o projeto está em desenvolvimento, alterações nos módulos, nos produtos, nos notebooks ou no dashboard podem exigir atualização do texto.

Sempre que uma funcionalidade for modificada, recomenda-se verificar se a mudança afeta o escopo e as fontes de dados, as regras de harmonização, os produtos Analytic e Consumo, as análises e visualizações, as limitações metodológicas ou os procedimentos de execução e auditoria.

A documentação deve acompanhar o comportamento efetivo do código e dos dados, distinguindo funcionalidades implementadas de propostas futuras.
