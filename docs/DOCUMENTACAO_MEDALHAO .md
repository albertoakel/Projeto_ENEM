# Documentação técnica --- Processo Medalhão do Projeto ENEM

> **Escopo:** microdados do Exame Nacional do Ensino Médio (ENEM),
> edições de 1998 a 2025.\
> **Unidade de processamento:** Unidade da Federação (UF).\
> **Arquitetura:** Bronze → Staging → Silver → Gold → Analytic → Consumo
> → Dashboard.\
> **Formato predominante:** Parquet com compressão ZSTD.\
> **Estado de referência da documentação:** implementação analisada em
> novembro de 2026.

------------------------------------------------------------------------

## 1. Finalidade e escopo do projeto

O Projeto ENEM organiza os microdados históricos do ENEM para permitir
análises estatísticas, temporais e espaciais em escala municipal. O
período investigado compreende 28 edições, de 1998 a 2025.

A engenharia dos dados precisa lidar com mudanças históricas nos
arquivos publicados pelo INEP: nomes e disponibilidade de variáveis,
formatos de origem, organização dos arquivos, estrutura das avaliações e
referências territoriais. O pipeline transforma essas fontes
heterogêneas em bases progressivamente mais organizadas, preservando a
rastreabilidade entre os arquivos originais e os produtos utilizados nas
análises.

A seleção de variáveis prioriza as informações necessárias à
investigação e não depende do questionário socioeconômico completo.

### 1.1 Objetivos técnicos

-   Preservar e inventariar as fontes originais.
-   Reduzir o volume de dados por seleção de variáveis e filtro por UF.
-   Padronizar a estrutura dos registros históricos.
-   Registrar explicitamente a referência territorial de cada período.
-   Produzir indicadores municipais e estatísticas por grupos.
-   Organizar produtos finais para análises e visualizações.
-   Manter manifestos, catálogos e auditorias que permitam localizar e
    verificar os produtos gerados.

### 1.2 Princípio de organização

As camadas têm responsabilidades distintas:

  -----------------------------------------------------------------------
  Camada                              Responsabilidade
  ----------------------------------- -----------------------------------
  Bronze                              Preservar e inventariar os arquivos
                                      originais

  Staging                             Extrair temporariamente os arquivos
                                      necessários ao processamento

  Silver                              Selecionar variáveis, filtrar
                                      registros por UF e converter para
                                      Parquet

  Gold                                Padronizar o schema individual e
                                      organizar referências territoriais

  Analytic                            Calcular indicadores e estatísticas
                                      agregadas

  Consumo                             Integrar e disponibilizar produtos
                                      para aplicações e análises

  Dashboard                           Carregar e apresentar os produtos
                                      de Consumo em interfaces
                                      interativas
  -----------------------------------------------------------------------

Staging é uma área operacional temporária, não uma camada persistente
equivalente às demais.

------------------------------------------------------------------------

## 2. Arquitetura geral

``` mermaid
flowchart TD
    A[ZIPs originais do INEP] --> B[Bronze]
    B --> C[Staging: extração temporária]
    C --> D[Silver: seleção e filtro por UF]
    D --> E[Gold: schema canônico e referências territoriais]
    E --> F[Analytic: indicadores e estatísticas]
    F --> G[Consumo: integração e produtos finais]
    G --> H[Dashboard Dash / Plotly / Folium]
    G --> I[Análises estatísticas e espaciais]
```

O fluxo é executado por UF. Os arquivos de uma UF são processados
separadamente dos arquivos de outra UF, permitindo limitar o volume de
dados tratado em cada execução.

### 2.1 Organização lógica do repositório

A estrutura conhecida do projeto inclui:

``` text
Projeto_ENEM/
├── executar_pipeline.py
├── data/
│   ├── bronze/
│   ├── staging/
│   ├── silver/
│   ├── gold/
│   ├── analytic/
│   ├── consumo/
│   ├── metadata/
│   │   └── dicionarios/
│   │       └── variaveis_enem_por_ano.csv
│   └── shapefiles/
├── docs/
├── notebooks/
│   ├── 01_Verificar_configuracao.ipynb
│   ├── 02_Execucao_Silver.ipynb
│   ├── 03_Execucao_Gold.ipynb
│   ├── 04_Execucao_Analitico.ipynb
│   ├── 05_Execucao_Consumo.ipynb
│   ├── 06_Analise_transversal.ipynb
│   ├── 07_Analise_transversal_mapas.ipynb
│   ├── 08_Analise_longitudinal.ipynb
│   └── ...
├── src/
│   ├── enem_pipeline/
│   │   ├── config.py
│   │   ├── estrutura.py
│   │   ├── bronze.py
│   │   ├── catalogo.py
│   │   ├── silver.py
│   │   ├── gold.py
│   │   ├── analytic.py
│   │   └── consumo.py
│   └── utils/
└── dash/
    ├── app.py
    ├── assets/
    ├── components/
    ├── dash_utils/
    │   ├── data_loader.py
    │   ├── perf.py
    │   └── ufs.py
    └── pages/
        ├── visao_geral.py
        ├── visao_geral_layout.py
        ├── visao_geral_graficos.py
        ├── mapa_geral.py
        ├── analise_municipal.py
        └── perfil_participantes.py
```

A árvore é uma representação lógica dos componentes analisados, não um
inventário garantido de todos os arquivos presentes em qualquer
checkout. Os notebooks de auditoria independentes `XXa_auditoria__`
foram removidos e, portanto, não são apresentados como arquivos atuais.
As verificações existentes nos módulos e notebooks de execução continuam
sendo descritas nas seções correspondentes.

### 2.2 Ambiente técnico

O ambiente utilizado na análise do projeto inclui:

-   Linux;
-   Python 3.11;
-   DuckDB 1.4.5;
-   Pandas;
-   Parquet com compressão ZSTD;
-   Dash, Plotly e Folium no dashboard.

A configuração central do pipeline está em
`src/enem_pipeline/config.py`. A inicialização de caminhos e importações
dos notebooks utiliza o auxiliar `_setup.py`.

------------------------------------------------------------------------

## 3. Catálogo histórico de variáveis

**Arquivo:** `data/metadata/dicionarios/variaveis_enem_por_ano.csv`\
**Módulo de apoio:** `src/enem_pipeline/catalogo.py`

O catálogo registra a seleção de variáveis considerada relevante para
cada edição do ENEM. Ele é temporal: a disponibilidade e a seleção
variam de ano para ano.

O inventário analisado cobre 1998--2025 e contém 71 variáveis distintas
ao longo do período. Onze variáveis aparecem em todos os anos
inventariados:

-   `NU_ANO`
-   `NU_INSCRICAO`
-   `NU_NOTA_REDACAO`
-   `NU_NOTA_COMP1`
-   `NU_NOTA_COMP2`
-   `NU_NOTA_COMP3`
-   `NU_NOTA_COMP4`
-   `NU_NOTA_COMP5`
-   `TP_STATUS_REDACAO`
-   `TP_FAIXA_ETARIA`
-   `TP_SEXO`

A existência de uma variável no catálogo não significa que ela esteja
necessariamente presente em todos os arquivos originais. A Silver
confronta a seleção catalogada com as colunas efetivamente disponíveis
na fonte daquele ano.

**Distinção importante:** `catalogo.py` dá suporte ao catálogo histórico
de variáveis. Os catálogos `catalogo_analytic_UF.csv` e
`catalogo_consumo_UF.csv` são metadados produzidos pelas respectivas
camadas e têm outra finalidade.

------------------------------------------------------------------------

## 4. Orquestração do pipeline

**Arquivo:** `executar_pipeline.py`

O orquestrador coordena o processamento das camadas. A execução é
parametrizada por UF e intervalo de anos, e as etapas são executadas em
sequência. Uma falha de execução ou validação interrompe o fluxo,
evitando que uma etapa posterior consuma silenciosamente uma saída
inválida.

Em termos operacionais, o fluxo compreende:

1.  Ler e validar os parâmetros de execução.
2.  Verificar as fontes originais disponíveis em Bronze.
3.  Preparar a área temporária Staging.
4.  Extrair e processar os arquivos anuais.
5.  Gerar ou reutilizar os produtos Silver após validação.
6.  Construir a Gold e seu manifesto.
7.  Construir os produtos Analytic e seus metadados.
8.  Construir os produtos de Consumo e executar as verificações
    correspondentes.

Os ZIPs originais precisam estar previamente disponíveis em
`data/bronze/`. A execução do pipeline não deve ser interpretada como um
processo que necessariamente baixa todas as fontes de forma automática.

### 4.1 Execução segmentada por notebooks

Os notebooks permitem executar e inspecionar etapas individualmente. Os
notebooks de execução não substituem os módulos Python: em geral,
configuram os parâmetros, verificam entradas, chamam as funções e
apresentam os resultados.

  ----------------------------------------------------------------------------
  Notebook                                 Papel
  ---------------------------------------- -----------------------------------
  `01_Verificar_configuracao.ipynb`        Verificar ambiente, diretórios,
                                           inventário de fontes, catálogo e
                                           leitura

  `02_Execucao_Silver.ipynb`               Executar Silver por UF e por ano,
                                           apresentando os resultados das
                                           fontes

  `03_Execucao_Gold.ipynb`                 Construir Gold a partir da Silver e
                                           inspecionar as saídas

  `04_Execucao_Analitico.ipynb`            Verificar manifesto Gold e executar
                                           os produtos Analytic

  `05_Execucao_Consumo.ipynb`              Verificar produtos Analytic,
                                           executar Consumo e inspecionar
                                           auditoria

  `06_Analise_transversal.ipynb`           Análise exploratória transversal

  `07_Analise_transversal_mapas.ipynb`     Análise exploratória espacial
                                           transversal

  `08_Analise_longitudinal.ipynb`          Análise exploratória longitudinal

  `09a_Analise_longitudinal_mapas.ipynb`   Análise espacial longitudinal

----------------------------------------------------------------------------

Os nomes apresentados identificam as funções dos notebooks analisados;
deve-se conferir o nome efetivo no diretório local antes de automatizar
chamadas por nome.

------------------------------------------------------------------------

## 5. Bronze --- preservação das fontes

**Implementação:** `src/enem_pipeline/bronze.py`

### 5.1 Objetivo

A Bronze representa a camada de entrada e preservação. Ela mantém os
pacotes originais do INEP como referência para o processamento, sem
aplicar as transformações analíticas das camadas seguintes.

### 5.2 Entradas e organização

As entradas são os arquivos ZIP anuais dos microdados do ENEM,
armazenados em `data/bronze/`.

A rotina de inventário identifica os arquivos disponíveis, inspeciona o
conteúdo dos pacotes e localiza os CSVs relevantes para cada edição.

### 5.3 Mudança estrutural em 2024 e 2025

Até 2023, a fonte principal é identificada no arquivo anual
`MICRODADOS_ENEM_AAAA.csv`.

Em 2024 e 2025, o processamento reconhece duas fontes:

-   `PARTICIPANTES_AAAA.csv`;
-   `RESULTADOS_AAAA.csv`.

Essa mudança é preservada nas etapas seguintes: os dois conjuntos não
são tratados como se fossem um único arquivo individual.

### 5.4 Saídas

-   ZIPs originais preservados em `data/bronze/`;
-   arquivos CSV extraídos temporariamente em `data/staging/`.

A Bronze é a referência de origem para reprocessamentos. A limpeza de
arquivos extraídos não deve alterar os pacotes originais.

------------------------------------------------------------------------

## 6. Staging --- extração temporária

**Implementação:** operações coordenadas pelo orquestrador e por
`src/enem_pipeline/silver.py`.

Staging é a área intermediária que recebe os CSVs extraídos dos ZIPs.
Ela reduz a necessidade de manter todo o conjunto de CSVs descompactados
durante o processamento.

A rotina trabalha ano a ano. Para cada ano, extrai os arquivos
necessários e os disponibiliza para leitura pela Silver.

A implementação confere o tamanho do CSV extraído com o tamanho
informado no conteúdo do ZIP. Se houver divergência, o arquivo pode ser
extraído novamente; se a inconsistência persistir, o processamento
falha.

A remoção do CSV temporário ocorre somente depois da gravação e
validação bem-sucedidas do Parquet Silver correspondente, quando a
limpeza está habilitada. Em caso de falha, a fonte temporária é
preservada para diagnóstico.

------------------------------------------------------------------------

## 7. Silver --- seleção, filtro por UF e conversão

**Implementação:** `src/enem_pipeline/silver.py`\
**Referências:** `config.py` e `catalogo.py`

### 7.1 Objetivo

A Silver reduz o volume dos microdados, selecionando as variáveis do
catálogo anual e mantendo somente os registros associados à UF
solicitada pela regra territorial vigente naquele período.

A camada preserva o nível individual dos registros. Não realiza
agregação municipal.

### 7.2 Seleção de variáveis

Para cada ano, a rotina obtém a lista de variáveis do catálogo e a
compara com as colunas efetivamente existentes no CSV.

A seleção aplicada é a interseção entre:

1.  as variáveis previstas no catálogo para o ano;
2.  as colunas presentes na fonte.

A coluna territorial necessária ao filtro por UF é incluída quando ainda
não está na seleção.

Consequências:

-   uma variável catalogada, mas ausente na fonte, não é criada
    artificialmente na Silver;
-   uma coluna presente no CSV, mas fora do catálogo, não é mantida
    apenas por existir;
-   diferenças de schema entre anos são esperadas e tratadas por meio do
    catálogo.

### 7.3 Regra de filtro territorial na Silver

A variável usada para selecionar a UF muda historicamente:

  Período      Variável de UF       Referência
  ------------ -------------------- ----------------
  1998--2000   `SG_UF_RESIDENCIA`   Residência
  2001--2007   `SG_UF_ESC`          Escola
  2008--2025   `SG_UF_PROVA`        Local de prova

A UF escolhida na execução é aplicada à coluna correspondente ao
período. Essa seleção define o universo de registros que seguirá para
Gold.

A mudança da variável territorial não é apenas uma troca de nome de
coluna: ela representa conceitos geográficos distintos e precisa ser
considerada nas análises longitudinais.

### 7.4 Leitura e gravação

A Silver utiliza DuckDB para consultar os CSVs, selecionar colunas,
filtrar registros e gravar Parquet com compressão ZSTD. A configuração
considera separador e codificação da fonte, incluindo exceções anuais
definidas no projeto.

### 7.5 Particularidade de 2024 e 2025

Para 1998--2023, a saída Silver é um arquivo anual principal.

Para 2024--2025, são gerados arquivos distintos para participantes e
resultados:

``` text
data/silver/uf=UF/ano=AAAA/
├── participantes.parquet
└── resultados.parquet
```

No intervalo completo, a expectativa operacional é de 30 fontes Silver:
26 arquivos de 1998--2023 e quatro arquivos correspondentes às duas
bases de 2024 e 2025.

### 7.6 Reutilização e validação

A função `processar_ano_silver()` permite reutilizar um Parquet
existente quando `reprocessar=False`, mas somente depois de validá-lo.

A validação verifica, entre outros pontos:

-   existência e possibilidade de leitura do Parquet;
-   quantidade de registros maior que zero;
-   presença da coluna territorial esperada;
-   pertencimento dos registros à UF solicitada;
-   correspondência de `NU_ANO` com o ano esperado, quando a coluna
    existe.

Se o arquivo existente não passar na validação, ele pode ser removido e
reprocessado a partir do CSV. A rotina preserva o CSV em caso de erro e
só o remove após a validação da saída.

### 7.7 Limites da validação Silver

A validação descrita é estrutural e territorial. Ela não equivale, por
si só, a uma auditoria semântica completa, a uma deduplicação de
participantes ou à comprovação de equivalência histórica entre
variáveis.

------------------------------------------------------------------------

## 8. Gold --- schema canônico e referências territoriais

**Implementação:** `src/enem_pipeline/gold.py`\
**Executor:** `03_Execucao_Gold.ipynb`

### 8.1 Objetivo

A Gold harmoniza a estrutura dos registros individuais da Silver. Ela
padroniza nomes e tipos de campos, organiza as informações territoriais
em colunas canônicas e preserva o nível de detalhe da fonte.

A Gold não é uma camada de indicadores agregados: as agregações
estatísticas são realizadas na Analytic.

### 8.2 Contrato canônico

O schema Gold analisado possui **29 colunas**:

  -----------------------------------------------------------------------
  Grupo                               Colunas
  ----------------------------------- -----------------------------------
  Identificação e território          `NU_ANO`,
                                      `TIPO_REFERENCIA_TERRITORIAL`,
                                      `SG_UF_TERRITORIO`,
                                      `CO_UF_TERRITORIO`,
                                      `CO_MUNICIPIO_TERRITORIO`,
                                      `NO_MUNICIPIO_TERRITORIO`

  Participante                        `TP_SEXO`, `TP_FAIXA_ETARIA`,
                                      `ANO_CONCLUIU`

  Presença                            `TP_PRESENCA`, `TP_PRESENCA_CN`,
                                      `TP_PRESENCA_CH`, `TP_PRESENCA_LC`,
                                      `TP_PRESENCA_MT`

  Notas                               `NU_NOTA_CN`, `NU_NOTA_CH`,
                                      `NU_NOTA_LC`, `NU_NOTA_MT`,
                                      `NU_NOTA_OBJETIVA`,
                                      `NU_NOTA_REDACAO`

  Redação                             `TP_STATUS_REDACAO`,
                                      `VL_PERC_COMP1`, `VL_PERC_COMP2`,
                                      `VL_PERC_COMP3`, `VL_PERC_COMP4`,
                                      `VL_PERC_COMP5`

  Escola                              `CO_ESCOLA`, `TP_ESCOLA`,
                                      `TP_DEPENDENCIA_ADM_ESC`
  -----------------------------------------------------------------------

O contrato define tipos canônicos. Quando uma variável não existe em
determinada fonte, a rotina `campo()` disponibiliza a coluna canônica
com valor nulo e tipo previsto em `TIPOS_GOLD`. Isso mantém a estrutura
das saídas sem inventar observações.

### 8.3 Referências territoriais

A Gold organiza a informação territorial em campos padronizados, mas
mantém o tipo de referência explicitamente registrado.

  ----------------------------------------------------------------------------
  Período                 Referência              Campos de origem usados como
                                                  referência municipal
  ----------------------- ----------------------- ----------------------------
  1998--2000              `RESIDENCIA`            `CO_MUNICIPIO_RESIDENCIA`,
                                                  `NO_MUNICIPIO_RESIDENCIA`

  2001--2007              `ESC`                   `CO_MUNICIPIO_ESC`,
                                                  `NO_MUNICIPIO_ESC`

  2008--2025              `PROVA`                 `CO_MUNICIPIO_PROVA`,
                                                  `NO_MUNICIPIO_PROVA`
  ----------------------------------------------------------------------------

A partir de 2008, a Gold também materializa a perspectiva de escola
quando os campos estão disponíveis. Assim, para 2008--2023, são
produzidas referências `ESC` e `PROVA`.

A padronização do nome da coluna não torna residência, escola e local de
prova conceitos equivalentes. O campo `TIPO_REFERENCIA_TERRITORIAL` deve
acompanhar as análises.

### 8.4 Fontes e quantidade de arquivos

A Silver fornece 30 fontes no intervalo completo. A Gold desdobra essas
fontes em produtos por referência territorial.

A expectativa analisada é de **48 arquivos Gold** para 1998--2025:

-   1998--2000: uma perspectiva de residência por ano;
-   2001--2007: uma perspectiva de escola por ano;
-   2008--2023: perspectivas de escola e prova por ano;
-   2024--2025: participantes na perspectiva de prova e resultados nas
    perspectivas de escola e prova.

Em 2024--2025, as bases `participantes` e `resultados` permanecem
separadas. Não é realizado join individual entre elas.

### 8.5 Estrutura de saída

Exemplo de organização:

``` text
data/gold/uf=UF/
└── ano=AAAA/
    ├── base=enem/
    │   ├── referencia=ESC/
    │   │   └── dados.parquet
    │   └── referencia=PROVA/
    │       └── dados.parquet
    ├── base=participantes/
    │   └── referencia=PROVA/
    │       └── dados.parquet
    └── base=resultados/
        ├── referencia=ESC/
        │   └── dados.parquet
        └── referencia=PROVA/
            └── dados.parquet
```

A presença de cada diretório depende do ano e da fonte correspondente.

### 8.6 Validações e manifesto

A rotina confere o schema canônico, a ordem e a quantidade de colunas e
a contagem de registros entre a fonte Silver e a saída Gold. A
substituição do arquivo definitivo ocorre depois das verificações
previstas.

É gerado o manifesto `manifesto_gold_UF.csv`, que registra informações
das fontes e dos arquivos Gold, incluindo ano, base, referência
territorial e caminho do produto.

O manifesto é a referência de localização usada pela Analytic.

### 8.7 Ressalva territorial importante

O filtro por UF acontece na Silver. Para os anos em que a Gold cria a
perspectiva `ESC` a partir de uma fonte Silver selecionada pela UF da
prova, a perspectiva escolar não recebe necessariamente um novo filtro
pela UF da escola.

Portanto, `uf=UF` no caminho da Gold identifica a UF utilizada para
selecionar a fonte Silver. Isso **não garante** que todos os municípios
de um produto `referencia=ESC` pertençam àquela UF. Essa distinção deve
ser mantida ao interpretar mapas e comparações por UF.

------------------------------------------------------------------------

## 9. Analytic --- indicadores e estatísticas municipais

**Implementação:** `src/enem_pipeline/analytic.py`\
**Executor:** `04_Execucao_Analitico.ipynb`

### 9.1 Objetivo e entrada

A Analytic transforma registros Gold em produtos estatísticos agregados.
A execução utiliza o manifesto Gold, verifica a existência das fontes
esperadas e constrói os produtos por UF e período.

O notebook analisado exige 48 fontes Gold registradas e existentes para
a execução integral de 1998--2025. Essa conferência prévia do notebook é
mais estrita do que uma chamada isolada ao módulo, que pode filtrar
entradas do manifesto cujos arquivos não estejam presentes.

### 9.2 Produtos

A implementação atual produz **nove produtos**:

  ------------------------------------------------------------------------------------------
  Produto                                    Conteúdo principal      Granularidade
  ------------------------------------------ ----------------------- -----------------------
  `demografia_municipal`                     Contagens e percentuais Ano × município ×
                                             por sexo e cobertura de referência
                                             faixa etária            

  `faixa_etaria_municipal`                   Contagem de registros   Ano × município ×
                                             por código de faixa     referência × faixa
                                             etária                  

  `presenca_municipal`                       Registros, presentes,   Ano × município ×
                                             ausentes e percentuais  referência

  `desempenho_redacao_municipal`             Estatísticas da nota de Ano × município ×
                                             redação                 referência

  `desempenho_objetiva_municipal`            Estatísticas da nota    Ano × município ×
                                             objetiva                referência

  `desempenho_areas_municipal`               Estatísticas de         Ano × município ×
                                             Ciências da Natureza,   referência
                                             Ciências Humanas,       
                                             Linguagens e Matemática 

  `escola_municipal`                         Contagens e percentuais Ano × município ×
                                             por dependência         referência
                                             administrativa          

  `desempenho_grupos_municipal`              Estatísticas por grupos Ano × município ×
                                             e disciplina            referência × grupo ×
                                                                     disciplina

  `desempenho_sexo_faixa_etaria_municipal`   Desempenho cruzado por  Ano × município ×
                                             sexo e faixa etária     referência × grupo ×
                                                                     disciplina
  ------------------------------------------------------------------------------------------

A granularidade efetiva varia conforme o produto e a disponibilidade
histórica das variáveis.

### 9.3 Estatísticas de desempenho

Para as notas disponíveis, a rotina calcula estatísticas como:

-   quantidade de notas válidas;
-   quantidade de notas iguais a zero;
-   média;
-   média das notas positivas;
-   mediana;
-   desvio-padrão;
-   primeiro quartil;
-   terceiro quartil.

As contagens de notas válidas são importantes para interpretar a
cobertura de cada média. Zero não é tratado como sinônimo de valor
ausente: a rotina mantém uma contagem própria de zeros.

### 9.4 Periodização da estrutura de avaliação

A estrutura das provas muda ao longo do período:

  -----------------------------------------------------------------------
  Período                             Indicadores
  ----------------------------------- -----------------------------------
  1998--2008                          Nota objetiva e redação

  2009--2025                          Ciências da Natureza (CN), Ciências
                                      Humanas (CH), Linguagens e Códigos
                                      (LC), Matemática (MT) e redação
  -----------------------------------------------------------------------

O produto `desempenho_objetiva_municipal` é aplicável ao período antigo.
O produto `desempenho_areas_municipal` corresponde à estrutura a partir
de 2009.

Não se deve tratar a nota objetiva antiga como equivalente direto a uma
das áreas ou à soma das áreas da estrutura posterior sem uma metodologia
específica de comparabilidade.

### 9.5 Grupos analíticos

Os produtos por grupos consideram dimensões disponíveis na fonte, como:

-   sexo;
-   dependência administrativa da escola;
-   faixa etária.

A disponibilidade não é uniforme em todos os anos. A rotina respeita as
colunas existentes e os períodos em que as dimensões podem ser
calculadas.

### 9.6 Tratamento de 2024 e 2025

A partir de 2024, as fontes de participantes e resultados são utilizadas
separadamente:

  Produto                 Fonte principal
  ----------------------- -----------------
  Demografia              `participantes`
  Faixa etária            `participantes`
  Presença                `resultados`
  Desempenho de redação   `resultados`
  Desempenho por áreas    `resultados`
  Escola                  `resultados`
  Desempenho por grupos   `resultados`

Não há chave individual disponível para associar com segurança os
registros das duas fontes. Por isso, o desempenho cruzado por sexo e
faixa etária não é calculado para 2024--2025. O produto
`desempenho_sexo_faixa_etaria_municipal` pode, portanto, ficar vazio em
determinados recortes; a rotina Analytic admite essa situação.

### 9.7 Saídas e metadados

Os nove produtos são gravados em:

``` text
data/analytic/uf=UF/
├── demografia_municipal.parquet
├── faixa_etaria_municipal.parquet
├── presenca_municipal.parquet
├── desempenho_redacao_municipal.parquet
├── desempenho_objetiva_municipal.parquet
├── desempenho_areas_municipal.parquet
├── escola_municipal.parquet
├── desempenho_grupos_municipal.parquet
└── desempenho_sexo_faixa_etaria_municipal.parquet
```

Também são produzidos:

-   `catalogo_analytic_UF.csv`: descrição dos produtos, granularidade,
    período, linhas e colunas;
-   `manifesto_analytic_UF.csv`: localização e metadados dos arquivos
    gerados.

A rotina grava em arquivo temporário, relê o Parquet e verifica
estrutura e quantidade de linhas antes de substituir a saída definitiva.

------------------------------------------------------------------------

## 10. Consumo --- integração dos produtos

**Implementação:** `src/enem_pipeline/consumo.py`\
**Executor:** `05_Execucao_Consumo.ipynb`

### 10.1 Objetivo

A Consumo organiza os produtos Analytic em bases adequadas à exploração
e ao dashboard. Ela não reprocessa os registros individuais da Gold nem
recalcula toda a estatística da Analytic; sua função central é integrar
e disponibilizar os indicadores já produzidos.

A implementação atual contempla **quatro produtos finais**.

### 10.2 Produtos finais

  ------------------------------------------------------------------------------------------
  Produto                                    Granularidade           Função
  ------------------------------------------ ----------------------- -----------------------
  `painel_municipal`                         Ano × município ×       Painel integrado de
                                             referência territorial  demografia, presença,
                                                                     desempenho e escola

  `faixa_etaria_municipal`                   Ano × município ×       Distribuição etária,
                                             referência × faixa      mantida separadamente

  `desempenho_grupos_municipal`              Ano × município ×       Desempenho segmentado
                                             referência × tipo de    
                                             grupo × grupo ×         
                                             disciplina              

  `desempenho_sexo_faixa_etaria_municipal`   Ano × município ×       Desempenho cruzado por
                                             referência × dimensões  sexo e faixa etária
                                             de grupo                
  ------------------------------------------------------------------------------------------

### 10.3 Construção do painel municipal

O painel integra seis produtos Analytic:

1.  `demografia_municipal`, como base inicial;
2.  `presenca_municipal`;
3.  `desempenho_redacao_municipal`;
4.  `desempenho_objetiva_municipal`;
5.  `desempenho_areas_municipal`;
6.  `escola_municipal`.

A chave territorial e temporal de integração considera:

-   `ano`;
-   `CO_MUNICIPIO_TERRITORIO`;
-   `TIPO_REFERENCIA_TERRITORIAL`.

As integrações usam junções externas (*outer joins*) para preservar
municípios presentes em apenas uma das fontes. O nome municipal é
verificado como dimensão descritiva, mas não substitui o código
municipal como chave.

As métricas genéricas recebem nomes específicos para evitar colisões
entre produtos. A rotina também deriva contagens de avaliados a partir
das contagens de notas válidas, quando aplicável.

### 10.4 Produtos auxiliares

Os produtos de faixa etária, desempenho por grupos e desempenho cruzado
são mantidos separados do painel principal porque possuem granularidades
diferentes. A separação evita multiplicar linhas ou misturar níveis de
agregação incompatíveis.

### 10.5 Auditoria da Consumo

A rotina verifica, entre outros pontos:

-   estrutura e conteúdo do manifesto Analytic;
-   compatibilidade da UF;
-   existência dos arquivos de origem;
-   unicidade das chaves nas granularidades esperadas;
-   dimensões municipais e consistência dos nomes;
-   colisões de métricas;
-   integridade dos Parquets temporários relidos;
-   reconciliação das contagens escolares com as categorias de
    dependência administrativa, quando possível.

O resultado é registrado em `auditoria_consumo_UF.csv`, com status geral
de auditoria.

### 10.6 Ressalva sobre produtos vazios

Há uma diferença de comportamento que deve ser considerada na
interpretação da auditoria: a Analytic admite que
`desempenho_sexo_faixa_etaria_municipal` fique vazio em recortes nos
quais não há base para o cruzamento, especialmente em 2024--2025. A
rotina de Consumo, por sua vez, exige a não vacuidade dos quatro
produtos finais.

Assim, uma auditoria de Consumo pode falhar por vacuidade de um produto
que está legitimamente vazio segundo a regra metodológica da Analytic.
Esse caso deve ser analisado como possível incompatibilidade entre
critérios de validação, e não automaticamente como falha na geração das
fontes.

### 10.7 Saídas

``` text
data/consumo/uf=UF/
├── painel_municipal.parquet
├── faixa_etaria_municipal.parquet
├── desempenho_grupos_municipal.parquet
└── desempenho_sexo_faixa_etaria_municipal.parquet
```

Metadados:

-   `catalogo_consumo_UF.csv`;
-   `manifesto_consumo_UF.csv`;
-   `auditoria_consumo_UF.csv`.

------------------------------------------------------------------------

## 11. Dashboard --- consumo e apresentação

**Diretório:** `dash/`\
**Aplicação principal:** `dash/app.py`

O dashboard consome os quatro Parquets da camada Consumo e associa os
indicadores às malhas municipais para produzir visualizações
interativas. A aplicação utiliza Dash, Plotly e Folium.

### 11.1 Inicialização e navegação

O `app.py` inicializa a aplicação Dash com o título `Dashboard ENEM` e
registra quatro páginas:

-   Visão Geral;
-   Mapas Municipais;
-   Análise Municipal;
-   Perfil dos Participantes.

A navegação é controlada por `dcc.Location` e links internos. A página
exibida é determinada pelo caminho da URL.

### 11.2 Seletores globais

A aplicação apresenta dois seletores compartilhados:

-   Unidade da Federação, com padrão `PA`;
-   referência territorial, com padrão `ESC`, permitindo `ESC` e
    `PROVA`.

A alteração desses seletores atualiza o conteúdo da página. O carregador
central recebe a UF e a referência e devolve os dados correspondentes.

### 11.3 Carregamento dos dados

**Módulo:** `dash/dash_utils/data_loader.py`

O carregador lê os quatro produtos da Consumo:

-   `painel_municipal.parquet`;
-   `faixa_etaria_municipal.parquet`;
-   `desempenho_grupos_municipal.parquet`;
-   `desempenho_sexo_faixa_etaria_municipal.parquet`.

Também carrega o shapefile municipal da UF:

``` text
data/shapefiles/{UF}_Municipios_2025/{UF}_Municipios_2025.shp
```

A associação entre indicadores e malha é feita por código municipal. O
tratamento inclui atualização/normalização de nomes e filtragem de
registros sem correspondência na malha.

### 11.4 Tratamento territorial no dashboard

O carregador aplica regras específicas para apresentação:

1.  A referência `RESIDENCIA` é convertida para `ESC` na visualização.
2.  Os códigos municipais são associados à malha da UF selecionada.
3.  Registros sem correspondência na malha são descartados.
4.  A aplicação mantém as referências `ESC` e `PROVA` conforme o seletor
    global.

Essa conversão de `RESIDENCIA` para `ESC` é uma regra de apresentação do
dashboard. Ela não altera retroativamente a referência registrada na
Gold ou nos produtos anteriores.

**Implicação:** a perspectiva `ESC` exibida no dashboard fica limitada
aos municípios encontrados no shapefile da UF selecionada. Registros de
escolas fora da malha selecionada não aparecem nessa visualização, mesmo
quando a Gold os preservou.

### 11.5 Cache e desempenho

O dashboard utiliza cache em mais de um nível:

-   cache de dados por UF e referência;
-   cache limitado de UFs carregadas;
-   `lru_cache` para combinações de dados;
-   cache de GeoJSON por UF;
-   simplificação de geometrias para reduzir o tamanho do conteúdo
    enviado ao navegador;
-   travas para evitar leituras concorrentes repetidas;
-   cópias dos DataFrames retornados para evitar alterações acidentais
    nos dados mantidos em cache;
-   cache de layouts no `app.py`, com `lru_cache(maxsize=16)` para
    combinações de página, UF e referência.

As geometrias são convertidas para EPSG:4326 e simplificadas com
tolerância de `0.002` grau, conforme a implementação analisada.

O `app.py` também registra métricas de desempenho e oferece opção de
pré-aquecimento de dados e GeoJSON por meio da variável de ambiente
`ENEM_PREAQUECER=1`.

### 11.6 Páginas e funcionalidades

#### Visão Geral

Apresenta o panorama histórico, indicadores de participação, desempenho
e comparações entre redes. As médias estaduais são calculadas de forma
ponderada pelo número de notas válidas, evitando tratar médias
municipais como observações de mesmo peso quando suas coberturas
diferem.

#### Mapas Municipais

Apresenta mapas coropléticos, rankings, histogramas e estatísticas
municipais. Os indicadores disponíveis respeitam a cobertura histórica:

-   participantes: 1998--2025;
-   redação: período completo conforme disponibilidade;
-   objetiva: até 2008;
-   quatro áreas: a partir de 2009.

#### Perfil dos Participantes

Apresenta distribuições por sexo e faixa etária e indicadores de
desempenho cruzados. Os códigos de `TP_FAIXA_ETARIA` são tratados como
categorias/códigos e agrupados em cinco categorias de apresentação. O
desempenho cruzado não é apresentado para 2024--2025, pois não há
associação individual entre as fontes de participantes e resultados.

A pirâmide de participantes utiliza a contagem do produto cruzado
filtrada para redação, evitando repetir participantes por disciplina. Os
intervalos de confiança de 95% para médias são estimativas aproximadas,
não medidas de dispersão individual nem testes automáticos de diferença
estatística.

#### Análise Municipal

Permite observar a evolução de um município e compará-lo com até quatro
municípios adicionais. Inclui tendências, dispersão e correlação de
Pearson. Os quadrantes são calculados com pontos que atendem ao critério
de `N válido > 100`; pontos abaixo desse limite podem permanecer
visíveis, mas não participam do cálculo dos quadrantes. Os gráficos
distinguem rede pública e privada.

### 11.7 Execução atual

O `app.py` analisado executa localmente em:

``` text
http://127.0.0.1:8050
```

A configuração atual utiliza `debug=True`, `host="127.0.0.1"` e
`port=8050`. Esses parâmetros descrevem a execução local analisada e não
devem ser considerados, sem adaptação, uma configuração de produção.

------------------------------------------------------------------------

## 12. Regras metodológicas transversais

### 12.1 Referência territorial não é homogênea no tempo

A referência histórica muda entre residência, escola e local de prova. O
schema canônico padroniza os campos, mas não elimina a diferença
conceitual. Toda análise longitudinal deve preservar ou explicitar
`TIPO_REFERENCIA_TERRITORIAL`.

### 12.2 Ausência não é zero

Valor nulo representa ausência ou indisponibilidade de informação. Zero
é um valor observado e, nas estatísticas de notas, recebe contagem
própria.

### 12.3 Schema comum não significa cobertura comum

Uma coluna existir na Gold não significa que tenha sido coletada ou
preenchida em todos os anos. A disponibilidade efetiva depende da fonte
original e deve ser examinada junto aos metadados e à cobertura do
produto.

### 12.4 Participantes e resultados em 2024--2025

As bases de participantes e resultados não são associadas
individualmente. Indicadores oriundos dessas fontes podem ser comparados
em nível agregado quando suas dimensões são compatíveis, mas não se deve
inferir correspondência individual.

### 12.5 Estrutura de avaliação

A nota objetiva até 2008 e as quatro áreas a partir de 2009 pertencem a
estruturas distintas. Uma série histórica contínua exige uma
justificativa metodológica adicional.

### 12.6 Contagem de registros e participantes

As contagens derivadas de `COUNT(*)` representam registros presentes na
fonte processada. Não se deve afirmar que houve deduplicação individual
se a rotina não a executou.

### 12.7 Cobertura das notas

Médias e outras estatísticas devem ser interpretadas junto de
`n_validos`, `n_zeros` e demais medidas de cobertura. Diferenças na
quantidade de notas válidas podem influenciar comparações municipais e
temporais.

------------------------------------------------------------------------

## 13. Auditoria, rastreabilidade e reprodutibilidade

Os manifestos e catálogos são parte da arquitetura de dados. Eles
permitem localizar produtos, identificar fontes e conferir a execução.

  ------------------------------------------------------------------------------
  Artefato                       Camada                  Finalidade
  ------------------------------ ----------------------- -----------------------
  `variaveis_enem_por_ano.csv`   Metadados               Registrar variáveis
                                                         selecionadas por edição

  `manifesto_gold_UF.csv`        Gold                    Relacionar fontes e
                                                         saídas Gold

  `catalogo_analytic_UF.csv`     Analytic                Descrever produtos,
                                                         períodos e dimensões

  `manifesto_analytic_UF.csv`    Analytic                Localizar os Parquets
                                                         Analytic

  `catalogo_consumo_UF.csv`      Consumo                 Descrever produtos
                                                         finais

  `manifesto_consumo_UF.csv`     Consumo                 Localizar os Parquets
                                                         de Consumo

  `auditoria_consumo_UF.csv`     Consumo                 Registrar verificações
                                                         e status da auditoria
  ------------------------------------------------------------------------------

### 13.1 Níveis de validação

As verificações não são idênticas entre camadas:

-   **Bronze/Staging:** inventário, identificação de fontes, extração e
    consistência do tamanho dos CSVs extraídos.
-   **Silver:** existência, leitura, não vacuidade, coluna territorial,
    UF dos registros e ano, quando disponível.
-   **Gold:** contrato canônico, tipos/colunas, contagem de registros e
    manifesto.
-   **Analytic:** conferência das fontes Gold pelo notebook, geração de
    produtos, leitura de saídas e metadados.
-   **Consumo:** unicidade de chaves, compatibilidade de dimensões,
    integridade dos arquivos e reconciliações previstas.
-   **Dashboard:** carregamento, associação espacial, filtros, cache e
    construção das visualizações.

Uma validação estrutural bem-sucedida não equivale automaticamente a uma
validação semântica de todos os indicadores. A interpretação deve
considerar o tipo de teste efetivamente executado.

### 13.2 Reprodutibilidade

Para reproduzir uma execução, é necessário preservar ou registrar:

-   versão do código;
-   UF e intervalo de anos;
-   arquivos ZIP de origem;
-   catálogo anual de variáveis;
-   parâmetros de configuração;
-   manifestos e catálogos produzidos;
-   ambiente Python e dependências;
-   shapefiles utilizados no dashboard, quando houver análise espacial.

Os arquivos Parquet e os manifestos de cada UF devem ser tratados como
produtos de uma execução específica, e não como saídas intercambiáveis
sem verificação.

------------------------------------------------------------------------

## 14. Limitações e pontos de atenção identificados

1.  **Mudança de referência territorial:** residência, escola e local de
    prova não são conceitos equivalentes.
2.  **Seleção da UF na Silver:** a UF usada para selecionar registros
    pode não corresponder à UF da escola em todas as perspectivas Gold.
3.  **2024--2025:** participantes e resultados são processados
    separadamente, sem join individual.
4.  **Comparabilidade das avaliações:** a estrutura de nota objetiva até
    2008 difere da estrutura por áreas a partir de 2009.
5.  **Disponibilidade temporal:** variáveis e grupos não estão
    disponíveis uniformemente em todo o período.
6.  **Deduplicação:** as contagens de registros não devem ser
    interpretadas como contagens deduplicadas sem uma etapa explícita de
    deduplicação.
7.  **Auditoria de Consumo:** a exigência de não vacuidade de todos os
    produtos pode conflitar com a vacuidade metodologicamente esperada
    do produto de desempenho cruzado em 2024--2025.
8.  **Filtro espacial no dashboard:** registros sem correspondência no
    shapefile selecionado são descartados da visualização.
9.  **Cache:** resultados apresentados pelo dashboard dependem das
    chaves e políticas de cache; alterações nos Parquets ou shapefiles
    devem ser acompanhadas de invalidação/reinicialização apropriada do
    processo quando necessário.
10. **Validação semântica:** testes estruturais e reconciliações não
    substituem uma auditoria substantiva de cada indicador e de sua
    comparabilidade histórica.

Esses pontos não invalidam a arquitetura. Eles delimitam o que os
produtos permitem afirmar e quais cuidados devem acompanhar as análises.

------------------------------------------------------------------------

## 15. Procedimento operacional resumido

### 15.1 Preparação

1.  Ativar o ambiente Python do projeto.
2.  Conferir dependências e configuração.
3.  Disponibilizar os ZIPs originais em `data/bronze/`.
4.  Conferir o catálogo `variaveis_enem_por_ano.csv`.
5.  Confirmar UF e intervalo temporal.

### 15.2 Execução integral

Na raiz do projeto:

``` bash
python executar_pipeline.py
```

A execução deve ser acompanhada pelos logs e pelos resultados de cada
camada. Em caso de erro, identificar a primeira etapa que falhou e
inspecionar suas fontes, manifestos e arquivos temporários antes de
avançar.

### 15.3 Execução por notebooks

Quando for necessário inspecionar uma etapa isoladamente, executar os
notebooks na ordem correspondente às dependências:

1.  verificação de configuração;
2.  Silver;
3.  Gold;
4.  Analytic;
5.  Consumo;
6.  análises exploratórias.

Antes de executar uma camada isoladamente, confirmar que as entradas e
os manifestos da camada anterior correspondem à mesma UF e ao intervalo
desejado.

### 15.4 Inicialização do dashboard

A partir da raiz do projeto, utilizar o ambiente com as dependências do
dashboard e executar o aplicativo conforme a organização local. A
configuração analisada inicia o servidor local na porta 8050.

------------------------------------------------------------------------

## 16. Síntese do fluxo de dados

  -------------------------------------------------------------------------------
  Etapa             Granularidade         Produto principal     Transformação
                                                                central
  ----------------- --------------------- --------------------- -----------------
  Bronze            Arquivo original      ZIP anual             Preservação e
                                                                inventário

  Staging           CSV anual             CSV extraído          Extração e
                                                                verificação

  Silver            Registro individual   Parquet por           Seleção de
                                          UF/ano/base           variáveis e
                                                                filtro por UF

  Gold              Registro individual   Parquet canônico por  Padronização
                                          ano/base/referência   estrutural e
                                                                territorial

  Analytic          Município/ano/grupo   Nove produtos         Indicadores e
                                          agregados             estatísticas

  Consumo           Município/ano/grupo   Quatro produtos       Integração e
                                          finais                organização

  Dashboard         Visualização          Páginas interativas   Filtros, mapas e
                    municipal                                   gráficos
  -------------------------------------------------------------------------------

A arquitetura separa deliberadamente a preparação dos registros
individuais (Silver e Gold), o cálculo dos indicadores (Analytic), a
organização para uso (Consumo) e a apresentação (Dashboard). Essa
separação facilita a manutenção, a auditoria e a evolução independente
das etapas.

------------------------------------------------------------------------

## 17. Arquivos centrais de referência

  -----------------------------------------------------------------------
  Arquivo                             Responsabilidade
  ----------------------------------- -----------------------------------
  `executar_pipeline.py`              Orquestração do processamento

  `src/enem_pipeline/config.py`       Configuração central

  `src/enem_pipeline/estrutura.py`    Estrutura e diretórios do projeto

  `src/enem_pipeline/bronze.py`       Inventário e extração das fontes

  `src/enem_pipeline/catalogo.py`     Leitura do catálogo histórico

  `src/enem_pipeline/silver.py`       Seleção, filtro por UF e geração
                                      Silver

  `src/enem_pipeline/gold.py`         Schema canônico, referências
                                      territoriais e manifesto Gold

  `src/enem_pipeline/analytic.py`     Indicadores e produtos estatísticos

  `src/enem_pipeline/consumo.py`      Integração, produtos finais e
                                      auditoria

  `dash/app.py`                       Inicialização, navegação, seletores
                                      globais e layouts

  `dash/dash_utils/data_loader.py`    Carregamento, tratamento
                                      territorial e cache

  `dash/dash_utils/perf.py`           Instrumentação e logs de desempenho

  `dash/pages/`                       Layouts e callbacks das páginas
  -----------------------------------------------------------------------

------------------------------------------------------------------------

**Fim da documentação técnica do processo Medalhão do Projeto ENEM.**
