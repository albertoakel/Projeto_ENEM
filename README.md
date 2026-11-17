# Projeto ENEM — Análise histórica, territorial e educacional

Projeto de engenharia e análise de dados dos microdados do **Exame Nacional do Ensino Médio (ENEM)**, abrangendo as edições de **1998 a 2025**.

O projeto organiza e harmoniza dados de diferentes edições do exame, produz indicadores agregados por município e ano e disponibiliza os resultados em análises exploratórias e em um dashboard interativo.

O processamento é estruturado por Unidade da Federação (UF), permitindo trabalhar com diferentes recortes geográficos e temporais, conforme a disponibilidade das fontes.

## Objetivos

- Organizar os microdados históricos do ENEM em uma estrutura de dados padronizada.
- Harmonizar variáveis e referências territoriais que mudaram ao longo das edições.
- Produzir indicadores municipais de participação, perfil dos participantes e desempenho.
- Explorar padrões temporais e espaciais por meio de análises transversais e longitudinais.
- Disponibilizar os resultados em um dashboard interativo.
- Manter rastreabilidade do processamento por meio de manifestos, relatórios e auditorias.

## Visão geral do projeto

O fluxo de dados segue uma arquitetura em camadas:

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

| Camada | Responsabilidade |
|---|---|
| **Bronze** | Armazenamento e inventário dos arquivos originais compactados |
| **Staging** | Extração temporária dos arquivos necessários ao processamento |
| **Silver** | Seleção das variáveis de interesse e dos registros da UF |
| **Gold** | Padronização do esquema e das referências territoriais |
| **Analytic** | Geração de indicadores e estatísticas agregados por município |
| **Consumo** | Integração e organização dos produtos para análises e visualizações |

A documentação técnica detalha as regras, os formatos, as validações e os produtos de cada etapa.

## Produtos e análises

A camada Analytic gera produtos municipais relacionados a:

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

Os notebooks contemplam análises transversais, espaciais e longitudinais, incluindo visualizações cartográficas.

## Dashboard interativo

O projeto inclui uma aplicação desenvolvida com **Dash**, com quatro páginas:

1. **Visão Geral** — indicadores históricos de participação e desempenho;
2. **Mapas Municipais** — visualizações temáticas e comparações territoriais;
3. **Análise Municipal** — evolução e comparação entre municípios;
4. **Perfil dos Participantes** — distribuições por sexo e faixa etária e cruzamentos disponíveis.

A aplicação utiliza os produtos da camada Consumo e arquivos geográficos municipais. Há mecanismos de cache e instrumentação de desempenho para reduzir carregamentos repetidos e acompanhar a execução.

## Tecnologias

- Python
- DuckDB
- Pandas
- Parquet / Zstandard
- Jupyter Notebook
- Dash
- Plotly
- Folium
- Shapefiles

## Estrutura do repositório

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

Os diretórios de dados armazenam arquivos de origem, produtos intermediários e resultados processados. Os dados são organizados por UF e, conforme a etapa, por ano, base de origem ou referência territorial.

## Como executar

### 1. Preparar o ambiente

Utilize um ambiente Python com as dependências do projeto instaladas. Os módulos de processamento e o dashboard dependem das bibliotecas listadas na seção [Tecnologias](#tecnologias).

> As versões e a instalação detalhada das dependências devem ser conferidas na configuração atual do repositório.

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

### 5. Utilizar os notebooks

O diretório `notebook/` reúne notebooks para configuração, execução das etapas, análises e auditorias. Para executar uma análise, os produtos das camadas anteriores correspondentes à UF e ao período devem estar disponíveis.

## Cuidados metodológicos

A série histórica do ENEM não possui estrutura inteiramente uniforme. Algumas mudanças importantes precisam ser consideradas na leitura dos resultados:

- **Referências territoriais:** entre 1998 e 2000, a referência utilizada é o município de residência; entre 2001 e 2007, o município da escola; a partir de 2008, são trabalhadas as referências de escola e prova, conforme a disponibilidade das fontes. Residência, escola e local de prova são perspectivas diferentes e não devem ser tratadas como equivalentes.
- **Seleção por UF:** a partir de 2008, a seleção de registros na camada Silver utiliza a UF do local de prova. A perspectiva `ESC` gerada posteriormente não implica um novo filtro pela UF da escola.
- **Estrutura das notas:** até 2008, é utilizada a nota objetiva; a partir de 2009, o desempenho é representado pelas quatro áreas do conhecimento, além da redação. Comparações entre esses períodos exigem cautela.
- **Edições de 2024 e 2025:** os dados de participantes e resultados são processados em bases separadas. Não é realizado cruzamento individual entre essas fontes; por isso, alguns indicadores cruzados por sexo e faixa etária podem não estar disponíveis nessas edições.
- **Dados agregados:** os produtos municipais são estatísticas agregadas e não devem ser interpretados como observações individuais.

Essas condições não impedem a análise histórica, mas precisam acompanhar a interpretação de comparações temporais e territoriais.

## Documentação

A documentação completa está no diretório [`docs/`](docs/):

- **[Documentação do Projeto](docs/DOCUMENTACAO_PROJETO.md)** — apresentação, objetivos, fontes, organização do repositório, produtos analíticos, análises, dashboard e limitações.
- **[Documentação Medalhão](docs/DOCUMENTACAO_MEDALHAO.md)** — arquitetura técnica Bronze, Staging, Silver, Gold, Analytic e Consumo, regras de processamento, validações e auditorias.

## Licença

O código-fonte deste projeto é distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para conhecer os termos de uso, cópia, modificação e redistribuição.

A licença MIT aplica-se ao código deste repositório. Ela não altera os termos de uso dos microdados do ENEM, shapefiles, bibliotecas ou de quaisquer outros materiais de terceiros utilizados pelo projeto. Esses materiais permanecem sujeitos às respectivas licenças e condições definidas por seus titulares.

## Status

Projeto em desenvolvimento. A documentação e os módulos devem ser atualizados à medida que novas funcionalidades, análises e produtos forem incorporados.

---

**Projeto ENEM — Análise histórica, territorial e educacional**
