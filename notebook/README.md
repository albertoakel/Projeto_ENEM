# Notebooks — Projeto ENEM

## 1. Apresentação

Esta pasta reúne os notebooks desenvolvidos no Projeto ENEM, organizados em dois conjuntos principais: processamento e preparação dos dados e estudos analíticos.

A organização reflete a separação entre a infraestrutura responsável pela transformação e disponibilização dos dados e as investigações realizadas a partir dos produtos gerados.

O projeto utiliza os microdados históricos do Exame Nacional do Ensino Médio (ENEM), abrangendo o período de 1998 a 2025, com processamento parametrizado por Unidade da Federação (UF).

## 2. Organização

Os notebooks estão distribuídos em dois diretórios:

| Diretório | Responsabilidade |
|---|---|
| `pipeline/` | Processamento dos microdados, execução da arquitetura Medalhão, construção dos produtos analíticos e auditorias. |
| `estudos_analiticos/` | Investigações estatísticas, temporais e territoriais organizadas em oito questões de pesquisa. |

### 2.1 Pipeline de dados

O diretório `pipeline/` contém os notebooks responsáveis pelo fluxo de processamento dos dados, desde a obtenção dos microdados originais até a disponibilização dos produtos de consumo.

As atividades estão organizadas em etapas:

- Download e preparação dos microdados;
- Verificação da configuração e dos dados de entrada;
- Processamento das camadas Silver e Gold;
- Construção das camadas Analytic e Consumo;
- Análises transversais e longitudinais;
- Análises espaciais;
- Auditoria integrada dos produtos.

**Documentação:** [`pipeline/README.md`](pipeline/README.md)

### 2.2 Estudos analíticos

O diretório `estudos_analiticos/` reúne oito eixos de investigação, estruturadas a partir de perguntas de pesquisa relacionadas à participação, ao perfil dos participantes e às desigualdades de desempenho no ENEM.

Os estudos estão organizados nos seguintes eixos:

| Eixo | Tema |
|---|---|
| Q1 | Evolução da participação no ENEM |
| Q2 | Desigualdade de gênero |
| Q3 | Desempenho por dependência administrativa |
| Q4 | Idade e trajetória dos participantes |
| Q5 | Desigualdade territorial |
| Q6 | Distribuição do desempenho |
| Q7 | Relações entre participação, perfil e desempenho |
| Q8 | Clusterização do desempenho multidisciplinar (Q8A — método; Q8B — aplicação) |

Cada eixo apresenta sua própria questão de pesquisa, procedimentos metodológicos, visualizações, resultados e conclusões. O Q8 é desenvolvido em dois notebooks complementares: Q8A documenta a fundamentação e a seleção do algoritmo; Q8B aplica o método selecionado e caracteriza os perfis municipais.

**Documentação:** [`estudos_analiticos/README.md`](estudos_analiticos/README.md)

O eixo Q8 investiga perfis municipais de desempenho multidisciplinar no ENEM. O notebook `Q8A_CLUSTERINGS_METODO.ipynb` compara algoritmos e seleciona o K-Means com K=2; o notebook `Q8B_CLUSTERINGS_APLICACAO.ipynb` aplica o método aos 37 municípios da coorte balanceada nas edições de 2009 a 2023.

## 3. Relação entre os diretórios

Os dois conjuntos possuem responsabilidades distintas, mas complementares.

O pipeline prepara, transforma, padroniza e disponibiliza os dados. Os estudos analíticos utilizam os produtos gerados para investigar questões específicas relacionadas ao ENEM.

O fluxo geral pode ser representado da seguinte forma:

```text
              MICRODADOS DO ENEM
                       |
                       v
                PIPELINE DE DADOS
                       |
                       v
               ARQUITETURA MEDALHÃO
                       |
                       v
                PRODUTOS DE CONSUMO
                       |
                       v
                ESTUDOS ANALÍTICOS
                       |
                       v
             RESULTADOS E CONCLUSÕES
```

Essa separação permite desenvolver novas investigações sem modificar as etapas fundamentais de processamento dos dados.

## 4. Configuração e execução

Os notebooks utilizam módulos Python compartilhados, localizados no diretório `src/` do projeto.

Cada conjunto possui seu próprio arquivo de inicialização:

- `pipeline/_setup.py`: configura os caminhos e o ambiente de execução dos notebooks do pipeline.
- `estudos_analiticos/_setup2.py`: configura o ambiente analítico, importa as configurações do projeto, as funções de carregamento e os módulos de análise.

A execução dos estudos analíticos depende da disponibilidade dos produtos de dados gerados pelo pipeline.

A configuração territorial é parametrizada, permitindo executar o processamento e as análises para diferentes Unidades da Federação, conforme a disponibilidade dos dados.

## 5. Considerações finais

A organização dos notebooks estabelece uma separação entre engenharia de dados e investigação analítica, mantendo a integração entre essas atividades.

Essa estrutura favorece a rastreabilidade do processamento, a organização das análises e a ampliação do projeto com novas questões de pesquisa e produtos analíticos.