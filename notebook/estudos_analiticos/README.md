# Estudos Analíticos — Projeto ENEM

## 1. Apresentação

Esta pasta reúne sete estudos analíticos desenvolvidos a partir dos microdados históricos do Exame Nacional do Ensino Médio (ENEM), com foco na investigação da participação, do perfil dos participantes e das desigualdades de desempenho no estado do Pará.

Os estudos utilizam os produtos de dados disponibilizados pela arquitetura Medalhão do projeto, especialmente as bases da camada Consumo, para desenvolver análises estatísticas, comparações temporais e investigações territoriais.

Cada notebook aborda uma questão específica de pesquisa, apresentando procedimentos metodológicos, indicadores, visualizações, resultados e conclusões.

O conjunto busca compreender diferentes dimensões do ENEM no território paraense, produzindo evidências descritivas que podem contribuir para a compreensão das desigualdades educacionais e subsidiar discussões relacionadas ao planejamento e à gestão pública da educação.

## 2. Organização dos estudos

Os sete estudos estão organizados por questões de pesquisa:

| Eixo | Tema | Notebook |
|---|---|---|
| Q1 | Evolução da participação no ENEM | `Q1_EVOLUCAO_DA_PARTICIPACAO.ipynb` |
| Q2 | Desigualdade de gênero | `Q2_DESIGUALDADE_DE_GENERO.ipynb` |
| Q3 | Desempenho por dependência administrativa | `Q3_DESEMPENHO_DEPENDENCIA.ipynb` |
| Q4 | Idade e trajetória dos participantes | `Q4_IDADE_TRAJETORIA.ipynb` |
| Q5 | Desigualdade territorial e desempenho municipal | `Q5_DESIGUALDADE_TERRITORIAL.ipynb` |
| Q6 | Distribuição e desigualdade do desempenho | `Q6_DISTRIBUICAO_DESEMPENHO.ipynb` |
| Q7 | Relações entre participação, perfil e desempenho | `Q7_PARTICIPACAO_PERFIL_DESEMPENHO.ipynb` |

## 3. Descrição dos eixos de investigação

### Q1 — Evolução da participação no ENEM

**Notebook:** `Q1_EVOLUCAO_DA_PARTICIPACAO.ipynb`

**Objetivo**

Investigar a evolução do número de participantes do ENEM no Pará, sua distribuição entre os municípios, a concentração territorial da participação e a presença dos inscritos na aplicação do exame.

**Período:** 1998–2025.

**Fontes:** `painel` e `dsp`.

**Abordagens analíticas**

- Evolução histórica do número de participantes;
- Crescimento e retração da participação municipal;
- Participação relativa dos municípios;
- Concentração territorial por indicadores HHI e Gini;
- Identificação de períodos de expansão e retração;
- Análise de presença e ausência na aplicação.

**Principais resultados**

- Entre 2003 e 2025, 127 dos 140 municípios comparáveis apresentaram crescimento no número de participantes (90,7%).
- O índice HHI municipal caiu de 0,1389 em 2001 para 0,0495 em 2025, indicando redução da concentração territorial.
- Belém permaneceu como principal polo de participação, reunindo 18,5% dos participantes em 2025.
- Os dez municípios com maior participação concentraram aproximadamente 47,9% dos participantes em 2025.
- Em 2024, houve aumento de 104,1% no número de participantes em relação a 2023.
- Em 2025, aproximadamente 78,7% dos inscritos foram registrados como presentes.

**Síntese**

A participação no ENEM apresentou expansão expressiva no Pará, alcançando a maioria dos municípios. Embora Belém continue concentrando a maior parcela dos participantes, os indicadores apontam para uma distribuição territorial menos concentrada. A evolução, entretanto, apresenta oscilações importantes e precisa considerar a cobertura municipal limitada nos primeiros anos da série.

### Q2 — Desigualdade de gênero no ENEM

**Notebook:** `Q2_DESIGUALDADE_DE_GENERO.ipynb`

**Objetivo**

Investigar diferenças de participação e desempenho entre participantes do sexo feminino e masculino no ENEM no Pará, considerando a composição dos inscritos, a evolução das diferenças de desempenho e sua distribuição territorial.

**Períodos:**
- Participação: 1998–2023.
- Desempenho: 2001–2023.
- Comparação municipal de referência: 2023.

**Fontes:** `painel` e `dsp`.

**Abordagens analíticas**

- Evolução do número de participantes por sexo;
- Composição percentual da participação;
- Distribuição territorial da participação feminina e masculina;
- Evolução das médias por sexo e disciplina;
- Diferenças de desempenho entre os grupos;
- Comparações municipais e cobertura amostral.

**Principais resultados**

- As mulheres permaneceram como maioria entre os participantes durante todo o período analisado.
- A diferença entre as proporções feminina e masculina diminuiu de 27,3 pontos percentuais em 2001 para aproximadamente 11 pontos percentuais em 2023.
- Em 2023, os homens apresentaram médias superiores em Ciências Humanas, Ciências da Natureza e Matemática.
- As mulheres apresentaram média superior em Redação, com diferença de aproximadamente 51,1 pontos.
- Em Matemática, a diferença foi de aproximadamente 37,4 pontos em favor dos homens.
- Em Linguagens, a diferença entre os grupos foi pequena.

**Síntese**

A predominância feminina na participação diminuiu ao longo do período, mas permaneceu presente até 2023. No desempenho, as diferenças variam conforme a disciplina: os homens apresentam vantagem recorrente em Matemática e Ciências da Natureza, enquanto as mulheres apresentam médias superiores em Redação.

### Q3 — Desempenho por dependência administrativa da escola

**Notebook:** `Q3_DESEMPENHO_DEPENDENCIA.ipynb`

**Objetivo**

Investigar as diferenças de participação e desempenho entre estudantes de escolas federais, estaduais, municipais e privadas, identificando desigualdades persistentes, mudanças na composição dos participantes e diferenças entre municípios.

**Períodos:**
- Participação: 1998–2025.
- Desempenho: 2001–2025.

**Fontes:** `painel` e `grupo`.

**Abordagens analíticas**

- Evolução da participação por dependência administrativa;
- Diferenças de desempenho entre escolas públicas e privadas;
- Evolução temporal do gap público–privado;
- Comparação entre as quatro categorias administrativas;
- Relação entre participação pública e desempenho;
- Diferenças territoriais no gap entre redes;
- Evolução da dispersão das notas.

**Principais resultados**

- A rede pública concentrou historicamente a maior parte dos participantes.
- A participação privada chegou a 24,7% em 2021, mas recuou para 10,8% em 2025.
- Em 2025, a rede pública voltou a representar 89,2% dos participantes classificados.
- As diferenças de desempenho entre redes variaram conforme a disciplina.
- Entre 2009 e 2025, as diferenças diminuíram em Ciências Humanas, Ciências da Natureza e Linguagens, mas aumentaram em Matemática e Redação.
- Em 2025, apenas 61 de 710 combinações município-disciplina (8,59%) atenderam ao critério de mais de 100 notas válidas em cada setor.

**Síntese**

A rede pública concentra a maior parte dos participantes do ENEM no Pará, mas apresenta médias inferiores às da rede privada. Essa desigualdade é persistente e varia entre as áreas do conhecimento. As escolas federais também apresentam resultados médios elevados, enquanto as comparações territoriais precisam considerar a cobertura limitada de municípios elegíveis.

### Q4 — Idade e trajetória dos participantes

**Notebook:** `Q4_IDADE_TRAJETORIA.ipynb`

**Objetivo**

Investigar a composição etária dos participantes do ENEM no Pará, sua evolução ao longo do tempo e as diferenças de desempenho entre as faixas etárias.

**Períodos:**
- Participação: 1998–2023.
- Desempenho: 2001–2023.

**Fonte:** `faixa` e `dsp`.

**Categorias etárias utilizadas**

- Menos de 17 anos;
- 17–20 anos;
- 21–25 anos;
- 26–40 anos;
- Acima de 40 anos.

**Abordagens analíticas**

- Evolução da distribuição etária;
- Participação dos estudantes mais jovens;
- Desempenho por faixa etária;
- Diferenças entre participantes mais jovens e mais velhos;
- Distribuição etária por sexo;
- Dispersão do desempenho por faixa etária.

**Principais resultados**

- A participação da faixa de 17–20 anos passou de 54,6% em 2001 para 92,2% em 2023.
- Considerando os participantes com até 20 anos, a proporção aumentou de 56,1% para 93,6%.
- Em 2023, a diferença de desempenho entre participantes com menos de 17 anos e aqueles acima de 40 anos chegou a aproximadamente 402,2 pontos em Redação e 176,7 pontos em Matemática.
- A cobertura territorial variou entre as faixas: 141 municípios apresentaram registros para participantes de 17–20 anos, enquanto apenas 34 municípios apresentaram registros para participantes acima de 40 anos.

**Síntese**

O perfil etário dos participantes tornou-se fortemente concentrado nas faixas mais jovens. Os participantes mais jovens também apresentaram, em geral, médias superiores. A interpretação das diferenças precisa considerar a cobertura territorial desigual entre os grupos e a impossibilidade de atribuir as diferenças exclusivamente à idade.

### Q5 — Desigualdade territorial e desempenho municipal

**Notebook:** `Q5_DESIGUALDADE_TERRITORIAL.ipynb`

**Objetivo**

Investigar as diferenças territoriais de desempenho no ENEM, considerando a evolução das médias municipais, a estabilidade dos resultados, a dispersão entre municípios, a evolução acumulada, a recorrência nos melhores rankings e a relação entre participação e desempenho.

**Período:** 1998–2025, conforme disponibilidade das fontes e questões.

**Fontes:** `painel` e `dsp`.

**Abordagens analíticas**

- Evolução das médias municipais;
- Estabilidade temporal do desempenho;
- Desigualdade entre municípios;
- Evolução acumulada das médias;
- Concentração territorial dos melhores resultados;
- Evolução do coeficiente de variação e do índice de Gini;
- Relação entre participação e desempenho municipal.

**Principais resultados**

- O coeficiente de variação das médias municipais em Matemática passou de 2,50% em 2009 para 5,84% em 2023.
- Belém e Castanhal estiveram no Top 10 em 100% dos anos entre 2009 e 2023 nas quatro disciplinas objetivas consideradas: CH, CN, LC e MT.
- Entre 2009 e 2023, a mediana anual da correlação de Pearson entre o logaritmo do número de participantes e a média municipal variou de 0,583 em Redação a 0,645 em Ciências Humanas.
- A evolução das médias estaduais não foi acompanhada por todos os municípios. Entre os 48 municípios comparáveis nos extremos de 2009 e 2023, houve municípios com redução das médias em Ciências Humanas, Ciências da Natureza, Linguagens e Matemática.
- A desigualdade territorial apresentou comportamentos distintos entre disciplinas, com destaque para o aumento da dispersão em Matemática.

**Síntese**

Os resultados evidenciam desigualdades territoriais no desempenho do ENEM no Pará. Essas diferenças aparecem tanto nos níveis das médias municipais quanto na evolução temporal e na concentração dos melhores resultados. A participação municipal apresenta associação positiva com o desempenho médio, mas essa relação não permite estabelecer causalidade.

### Q6 — Distribuição e desigualdade do desempenho

**Notebook:** `Q6_DISTRIBUICAO_DESEMPENHO.ipynb`

**Objetivo**

Compreender como as notas do ENEM se distribuem ao longo do tempo, se a dispersão dos resultados aumentou ou diminuiu, qual é a distância entre os segmentos de menor e maior desempenho e como essas diferenças se manifestam entre municípios, disciplinas e grupos de participantes.

**Períodos:**
- Painel municipal e grupos escolares: 1998–2025.
- Detalhamento por sexo e faixa etária: 2001–2023.

**Fontes:** `painel`, `faixa`, `grupo` e `dsp`.

**Abordagens analíticas**

- Evolução temporal da dispersão das notas;
- Comparação entre quartis e intervalos interquartis;
- Diferenças territoriais e entre grupos sociais;
- Distribuição dos resultados entre disciplinas;
- Comparação das amplitudes de desempenho por sexo, idade e dependência administrativa;
- Relação entre composição etária e desempenho.

**Principais resultados**

- Entre 2009 e 2025, Matemática apresentou ampliação da dispersão: o desvio-padrão combinado aproximado passou de 77,6 para 105,5 pontos, enquanto o IQR mediano municipal aumentou de 81,4 para 110,0 pontos.
- Ciências Humanas, Ciências da Natureza e Linguagens apresentaram redução do desvio-padrão combinado aproximado no mesmo período.
- Em 2023, a amplitude mediana municipal entre faixas etárias chegou a 284,6 pontos em Redação e 112,8 pontos em Matemática.
- Em 2025, as médias ponderadas das escolas privadas superaram as estaduais em aproximadamente 234,1 pontos em Redação e 120,6 pontos em Matemática.
- Em 2023, as notas zero corresponderam a aproximadamente 5,7% dos registros de Redação, enquanto nas provas objetivas permaneceram abaixo de 0,6%.

**Síntese**

A desigualdade de desempenho não apresenta uma trajetória única. Matemática se destaca pela ampliação da dispersão em relação a 2009, enquanto outras disciplinas apresentam reduções em determinados indicadores. As diferenças entre faixas etárias e redes escolares também são expressivas, especialmente em Redação e Matemática.

### Q7 — Relações entre participação, perfil e desempenho

**Notebook:** `Q7_PARTICIPACAO_PERFIL_DESEMPENHO.ipynb`

**Objetivo**

Investigar se as mudanças na participação e na composição dos participantes estão associadas ao desempenho municipal, além de examinar a relação entre diversidade etária, dispersão das notas e desigualdade entre redes.

**Período:** 1998–2025, conforme disponibilidade de cada fonte e questão.

**Fontes:** `painel`, `faixa` e `grupo`.

**Abordagens analíticas**

O eixo está estruturado em cinco investigações:

1. Crescimento da participação e mudança no desempenho;
2. Participação da rede pública e desempenho municipal;
3. Composição por sexo e desempenho municipal;
4. Diversidade etária e dispersão do desempenho;
5. Gap entre redes e desigualdade territorial.

São utilizadas correlações de Pearson e Spearman, comparações por grupos, quartis e indicadores de dispersão.

**Principais resultados**

- O crescimento da participação entre 2009 e 2025 não apresentou associação positiva generalizada com a evolução do desempenho municipal. Em Matemática, a correlação de Spearman foi de −0,332.
- A participação relativa da rede pública apresentou associação negativa persistente com o desempenho municipal entre 2009 e 2025. Em 2025, os coeficientes de Spearman variaram de −0,482 a −0,580 nas cinco disciplinas.
- A composição por sexo apresentou correlações geralmente fracas e variáveis ao longo do período.
- Municípios com maior diversidade etária apresentaram menor dispersão nas quatro provas objetivas, quando comparados os grupos extremos de diversidade. Esse comportamento não foi consistente em Redação.
- A diferença de desempenho entre redes pública e privada foi mais expressiva nos grupos de municípios com médias mais elevadas, especialmente em Matemática e Redação.

**Síntese**

As relações entre participação, perfil dos participantes e desempenho municipal não seguem um padrão único. A participação relativa da rede pública apresentou a associação mais persistente com as médias municipais, enquanto a expansão da participação e as mudanças na composição por sexo não mostraram correspondência sistemática com a evolução do desempenho.

A diversidade etária apresentou associação com menor dispersão nas provas objetivas, e a desigualdade entre redes variou conforme a posição dos municípios na distribuição do desempenho.

## 4. Procedimentos metodológicos comuns

Embora cada eixo possua objetivos e procedimentos específicos, existem elementos metodológicos compartilhados.

### 4.1 Unidade de análise

A referência territorial utilizada nos notebooks é o município da escola (`ESC`).

As análises utilizam diferentes níveis de agregação, conforme a pergunta de pesquisa:

- Estado e ano;
- Município e ano;
- Município, ano e disciplina;
- Município, ano e grupo de participantes;
- Dependência administrativa e disciplina.

### 4.2 Indicadores e procedimentos

Entre os indicadores e procedimentos empregados estão:

- Médias ponderadas pelo número de notas válidas;
- Medianas, quartis e intervalo interquartil (IQR);
- Desvio-padrão e coeficiente de variação;
- Índice de Gini e índice HHI;
- Crescimento absoluto e percentual;
- Rankings e recorrência de posições;
- Diferenças entre grupos e redes escolares;
- Correlações de Pearson e Spearman;
- Índice de Shannon normalizado;
- Análises de tendências e comparações temporais.

A seleção dos indicadores varia conforme o objetivo de cada eixo.

### 4.3 Comparabilidade histórica

A série histórica do ENEM apresenta mudanças na estrutura das provas, escalas e variáveis disponíveis.

Por esse motivo, os estudos respeitam os recortes temporais e as condições de comparabilidade de cada indicador.

Em particular, as análises de desempenho consideram a distinção entre:

- 1998–2008: estrutura anterior ao Novo ENEM;
- 2009–2025: estrutura com quatro áreas de conhecimento e redação.

Nem todas as variáveis estão disponíveis em todos os anos. As análises por sexo e faixa etária, por exemplo, possuem períodos de cobertura diferentes das análises de participação geral.

### 4.4 Limitações e interpretação

Os resultados são predominantemente descritivos e baseados em dados agregados.

Algumas limitações importantes devem ser consideradas:

- Cobertura municipal reduzida nos primeiros anos da série;
- Disponibilidade variável de variáveis ao longo do tempo;
- Diferenças no número de observações entre grupos;
- Critérios mínimos de elegibilidade para comparações municipais;
- Mudanças metodológicas e de escala do ENEM;
- Possibilidade de associações entre indicadores sem relação causal demonstrada.

As correlações entre municípios não representam relações individuais entre estudantes. Da mesma forma, diferenças entre médias de grupos não permitem atribuir causalidade à idade, ao sexo ou à dependência administrativa.

## 5. Configuração e carregamento dos dados

Os sete notebooks utilizam o arquivo `_setup2.py` para inicializar o ambiente analítico.

Esse arquivo:

- Identifica o diretório de execução;
- Resolve a raiz do projeto;
- Adiciona o diretório `src/` ao caminho de importação;
- Importa configurações do pacote `enem_pipeline.config`;
- Importa a função `read_allfiles2`;
- Importa o módulo de funções analíticas `utils.eda2`;
- Configura bibliotecas e parâmetros de visualização.

A função `read_allfiles2()` realiza o carregamento dos produtos de consumo necessários às análises.

Conforme o eixo, são utilizadas as seguintes fontes:

| Fonte | Utilização |
|---|---|
| `painel` | Participação e indicadores municipais de desempenho. |
| `faixa` | Informações por faixa etária. |
| `grupo` | Informações por grupos e dependência administrativa. |
| `dsp` | Indicadores detalhados de desempenho e dispersão. |

As funções de preparação, cálculo e análise estão centralizadas em `utils.eda2`, evitando duplicação de rotinas entre os notebooks.

### Parâmetros principais

Os notebooks utilizam os seguintes parâmetros:

```python
UF_PROCESSAMENTO = "PA"
TIPO_REFERENCIA = "ESC"
```

A UF pode ser alterada para outra unidade federativa, desde que os produtos de consumo correspondentes estejam disponíveis e sejam compatíveis com as funções utilizadas.

A referência `ESC` indica a utilização do município da escola como referência territorial.

## 6. Ordem de execução

Os notebooks podem ser executados independentemente entre si, pois cada eixo representa uma investigação própria.

Entretanto, todos dependem dos produtos gerados pelo pipeline de dados.

A sequência recomendada é:

1. Executar e validar as camadas de processamento;
2. Garantir a disponibilidade dos produtos da camada Consumo;
3. Configurar a UF e a referência territorial;
4. Executar os notebooks Q1–Q7 conforme a investigação desejada.

Não existe dependência obrigatória entre Q1, Q2, Q3, Q4, Q5, Q6 e Q7.

## 7. Relação com a arquitetura do projeto

Os estudos analíticos representam a etapa de investigação e interpretação dos dados disponibilizados pelo pipeline.

A relação entre os componentes é:

**Pipeline de dados → Produtos de Consumo → Estudos Analíticos**

O pipeline é responsável por preparar, padronizar e disponibilizar os dados. Os estudos analíticos utilizam esses produtos para investigar questões específicas sobre a participação e o desempenho no ENEM.

Essa separação permite ampliar as investigações sem modificar as etapas de processamento dos dados.

## 8. Considerações finais

Os sete estudos abordam dimensões complementares da participação e do desempenho no ENEM no Pará.

Em conjunto, investigam a evolução da participação, as diferenças entre grupos de participantes, as desigualdades entre redes escolares, a composição etária, a distribuição territorial e a variabilidade dos resultados.

Os resultados mostram que as desigualdades observadas não se manifestam de uma única forma. Elas variam conforme o território, a disciplina, o período histórico e a composição dos participantes.

A organização por questões de pesquisa permite ampliar o projeto com novos estudos, mantendo a separação entre a infraestrutura de dados e a investigação analítica.