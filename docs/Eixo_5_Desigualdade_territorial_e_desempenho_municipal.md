# **Eixo 5 — Desigualdade territorial e desempenho municipal**

**Área de análise:** Pará (PA)  
**Referência territorial:** município da escola (ESC)  
**Período disponível:** 2001–2023 para os resultados exportados; 2002–2023 para a análise principal.  
**Critério de elegibilidade:** mais de 100 participantes no município/ano (N > 100).

O eixo investiga as diferenças territoriais de desempenho no ENEM, considerando a evolução das médias municipais, a estabilidade dos resultados, a dispersão entre municípios, a evolução acumulada, a presença recorrente nos melhores rankings e a relação entre participação e desempenho.

A unidade de análise é o município onde o participante estudou. As médias municipais foram consolidadas a partir dos estratos de sexo e faixa etária, ponderando as notas pelo número de notas válidas (`n_validos`). Portanto, os indicadores de dispersão, Gini, percentis e quartis descrevem a distribuição das **médias municipais elegíveis**, e não a distribuição das notas individuais de todos os participantes do Pará.

## **Ressalvas metodológicas para a leitura dos resultados**

Há quatro cuidados importantes:

1. **Baixa adesão no início da série:** o arquivo contém resultados de 2001, mas não apresenta registros para 1998–2000. Em 2001, embora 116 municípios apareçam na base, apenas 40 superam N > 100; esse ano foi mantido como referência exploratória e não integra a análise longitudinal principal. A partir de 2002, o número de municípios elegíveis varia de 42 a 108.
2. **Mudança de escala em 2009:** as médias de `OBJETIVA` e `REDAÇÃO` entre 2002 e 2008 estão em magnitudes próximas de 0–100, enquanto os resultados a partir de 2009 estão na escala próxima de 0–1000. Assim, não se deve conectar diretamente essas séries nem calcular variações percentuais entre 2002 e 2023.
3. **Último ano disponível:** as planilhas de desempenho terminam em 2023. Embora o projeto tenha dados de participação posteriores, este arquivo não contém resultados municipais do Eixo 5 para 2024 e 2025.
4. **Cobertura variável:** o número de municípios elegíveis não é constante. As comparações temporais devem considerar a mudança de cobertura e, quando se compara a evolução entre dois anos, utilizar municípios presentes e elegíveis nos dois extremos.

## **T01 — Como evoluiu o desempenho médio dos municípios?**

A série principal mostra a evolução das médias municipais elegíveis e da média ponderada estadual. Para a leitura comparável entre disciplinas, o período mais adequado é 2009–2023, quando o exame passa a apresentar as áreas CH, CN, LC e MT, além da Redação, em uma escala próxima de 0–1000.

Entre 2009 e 2023, a média ponderada estadual apresentou os seguintes valores:

| Disciplina | 2009  | 2023  | Variação em pontos |
| ---------- | -----:| -----:| ------------------:|
| CH         | 484,1 | 509,4 | +25,2              |
| CN         | 478,3 | 483,0 | +4,7               |
| LC         | 475,4 | 501,7 | +26,3              |
| MT         | 470,9 | 511,0 | +40,2              |
| Redação    | 409,3 | 638,9 | +229,5             |

*Valores arredondados. A variação é uma diferença entre médias ponderadas estaduais dos anos inicial e final, não uma estimativa causal.*

A maior elevação nominal ocorreu na Redação, seguida por Matemática. Ciências da Natureza apresentou a menor variação entre os dois extremos. Essas diferenças devem ser lidas com atenção às oscilações anuais e às mudanças de cobertura municipal.

A quantidade de municípios elegíveis também variou. Em 2009 eram 57; o número cresceu até alcançar 108 em 2016 e 2017, mas recuou para 58 em 2023. Portanto, a média de cada ano não representa exatamente o mesmo conjunto de municípios.

**Interpretação:** os resultados indicam elevação das médias ponderadas entre 2009 e 2023, mais expressiva em Redação e Matemática. Entretanto, a trajetória não foi linear e a cobertura municipal diminuiu nos anos finais. A evolução estadual não deve ser interpretada como melhoria uniforme em todos os municípios.

No período anterior a 2009, a série exploratória apresenta somente os anos de 2001 a 2008 para `OBJETIVA` e `REDAÇÃO` (2001 aparece em uma tabela separada). Esses valores não devem ser unidos às séries posteriores devido à mudança de escala e à reorganização do exame.

## **T02 — Quais municípios apresentaram maior estabilidade de desempenho?**

**Resultado: estabilidade temporal das médias municipais (2009–2023)**

A planilha original de estabilidade exportou apenas registros de Redação e utilizou uma janela iniciada em 2002. Essa configuração não permite comparar adequadamente as cinco disciplinas no período posterior à mudança do ENEM.

Para evitar a mistura de escalas, a leitura comparável foi recalculada a partir da base municipal completa, considerando 2009–2023, N > 100, pelo menos 10 anos observados e cobertura mínima de 70% da janela. Com esses critérios, foram identificados 57 municípios por disciplina.

A estabilidade temporal, medida pelo coeficiente de variação (CV) das médias anuais municipais, apresentou as seguintes medianas entre municípios:

| Disciplina | CV temporal mediano | Amplitude temporal mediana (pontos) | Inclinação mediana (pontos/ano) |
| ---------- | ------------------- | ----------------------------------- | ------------------------------- |
| CH         | 5,41%               | 93,21                               | 0,91                            |
| CN         | 3,41%               | 56,42                               | 1,64                            |
| LC         | 3,01%               | 45,52                               | 1,61                            |
| MT         | 4,75%               | 73,67                               | 3,32                            |
| Redação    | 16,93%              | 264,02                              | 15,34                           |

*Estatísticas calculadas sobre as séries municipais elegíveis entre 2009 e 2023. A inclinação é descritiva e não significa crescimento contínuo em todos os anos.*

LC e CN apresentaram os menores CVs temporais medianos, indicando maior estabilidade relativa das médias municipais ao longo da janela. Redação apresentou a maior variação temporal, tanto em CV quanto em amplitude. Parte dessa diferença decorre da maior amplitude de pontuação observada na Redação, razão pela qual a comparação entre disciplinas deve priorizar o CV, e ainda assim ser interpretada com cautela.

**Municípios mais e menos estáveis por disciplina (menor e maior CV temporal):**

| Disciplina | Mais estáveis (CV)                                              | Menos estáveis (CV)                                                     |
| ---------- | --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| CH         | Belém (4,18%), Castanhal (4,54%), Canaã dos Carajás (4,65%)     | Novo Progresso (6,86%), Santa Maria do Pará (6,60%), Mãe do Rio (6,57%) |
| CN         | Belém (2,37%), Tucuruí (2,40%), Ananindeua (2,67%)              | Monte Alegre (4,42%), Breu Branco (4,32%), Soure (4,10%)                |
| LC         | Belém (2,14%), Barcarena (2,29%), Castanhal (2,38%)             | Mãe do Rio (4,23%), Tucumã (4,09%), Óbidos (3,96%)                      |
| MT         | Ourilândia do Norte (3,77%), Mocajuba (3,84%), Xinguara (4,04%) | Canaã dos Carajás (6,44%), Itaituba (6,17%), Marabá (6,15%)             |
| Redação    | Oriximiná (12,26%), Curuçá (12,74%), Breves (12,98%)            | Novo Repartimento (29,98%), Acará (28,08%), Concórdia do Pará (23,38%)  |

Em CH, CN e LC, os municípios de maior porte (Belém, Castanhal, Ananindeua, Tucuruí) concentram-se entre os mais estáveis, o que é compatível com menor ruído amostral em médias calculadas sobre mais participantes. Em MT e Redação esse padrão não se repete: o topo de estabilidade é ocupado por municípios de médias intermediárias ou baixas, como Mocajuba (média de 442 pontos em MT) e Oriximiná. Em MT e Redação, os municípios com maior CV também tendem a ter maior inclinação (Canaã dos Carajás: 5,62 pontos/ano em MT e 21,82 na Redação; Acará: 23,94 na Redação). Isso indica que parte da instabilidade medida reflete tendência de variação ao longo do período, e não apenas oscilação sem direção.

Alguns municípios entram na análise com cobertura menor que a janela completa (11 a 12 anos observados), como Soure, Santa Maria do Pará, Breu Branco e Rondon do Pará. Seus CVs devem ser lidos com mais cautela.

**Interpretação:** entre 2009 e 2023, as médias municipais de LC e CN foram relativamente mais estáveis, e Belém foi o município mais estável em CH, CN e LC. Redação apresentou maior oscilação temporal, com municípios de CV superior a 20% associados também a maiores inclinações. A estabilidade não deve ser confundida com nível de desempenho: um município pode manter uma média estável em patamar baixo ou alto. O CV temporal também não separa oscilação de tendência, de modo que municípios com melhora consistente podem aparecer como menos estáveis.

## **T03 — Qual é a diferença de desempenho e a dispersão entre municípios?**

A dispersão foi calculada anualmente entre as médias dos municípios elegíveis (N > 100). São considerados desvio-padrão, coeficiente de variação (CV), Gini das médias municipais e distância entre os percentis 90 e 10 (P90–P10). Como a escala da nota mudou em 2009 (0–100 até 2008, 0–1000 depois), a evolução ao longo do tempo é lida pelo CV e pelo Gini. O P90–P10 e o desvio-padrão, em pontos, só são comparáveis dentro de 2009–2023.

Em 2023, os indicadores foram:

| Disciplina | Municípios | Desvio-padrão | CV    | Gini   | P90–P10 |
| ---------- | ---------- | ------------- | ----- | ------ | ------- |
| CH         | 58         | 19,18         | 3,93% | 0,0219 | 51,43   |
| CN         | 58         | 17,10         | 3,68% | 0,0206 | 41,43   |
| LC         | 58         | 18,50         | 3,84% | 0,0217 | 48,34   |
| MT         | 58         | 28,03         | 5,84% | 0,0330 | 74,54   |
| Redação    | 58         | 53,95         | 9,16% | 0,0511 | 123,16  |

A Redação apresentou a maior dispersão absoluta e relativa entre as médias municipais em 2023. Matemática aparece em seguida, com CV de 5,84% e P90–P10 de 74,54 pontos. Ciências da Natureza apresentou a menor dispersão relativa, com CV de 3,68%.

**Evolução do CV (2009–2023)**

O resultado depende do ano de partida. Por isso, o CV de 2023 foi comparado com três anos-base: 2009 (início da série), 2016 (menor dispersão na maioria das áreas) e 2019 (pré-pandemia).

| Disciplina | CV 2009 | CV 2016 | CV 2019 | CV 2023 | Δ vs 2009 | Δ vs 2016 | Δ vs 2019 | Mínimo da série | Máximo da série |
| ---------- | ------- | ------- | ------- | ------- | --------- | --------- | --------- | --------------- | --------------- |
| CH         | 3,64%   | 2,82%   | 3,39%   | 3,93%   | +8%       | +40%      | +16%      | 2,55% (2015)    | 4,56% (2020)    |
| CN         | 3,84%   | 2,45%   | 3,14%   | 3,68%   | −4%       | +50%      | +17%      | 2,35% (2017)    | 3,91% (2020)    |
| LC         | 4,16%   | 2,50%   | 3,31%   | 3,84%   | −8%       | +53%      | +16%      | 2,50% (2016)    | 4,40% (2022)    |
| MT         | 2,50%   | 2,93%   | 3,71%   | 5,84%   | +133%     | +99%      | +58%      | 2,50% (2009)    | 5,84% (2023)    |
| Redação    | 13,57%  | 6,07%   | 8,08%   | 9,16%   | −33%      | +51%      | +13%      | 6,07% (2016)    | 15,13% (2014)   |

- **CH:** o CV passou de 3,64% para 3,93% entre 2009 e 2023, aumento moderado. Em relação a 2016 e 2019, a alta é maior.
- **CN:** passou de 3,84% para 3,68%, pequena redução em relação a 2009. O menor valor da série foi 2,35% em 2017.
- **LC:** passou de 4,16% para 3,84%, também uma redução em relação a 2009. O CV chegou a 4,40% em 2022.
- **MT:** passou de 2,50% para 5,84%, aumento expressivo. 2023 é o maior CV da série e 2009 o menor, de modo que a comparação com 2009 amplia a mudança. Ainda assim, a alta persiste contra 2016 (+99%) e 2019 (+58%).
- **Redação:** o CV passou de 13,57% para 9,16%, e o P90–P10 caiu de 145,68 para 123,16 pontos. A dispersão diminuiu tanto em termos relativos quanto absolutos em relação a 2009. No período anterior (2002–2008, escala 0–100), o CV já havia caído de 24,6% para 15,6%.

**Distribuição das médias municipais em relação à mediana**

Na Redação, o intervalo P10–P90 passou de 37,1 para 20,7 pontos percentuais da mediana entre 2009 e 2023, com o menor valor em 2016 (14,7 p.p.). Nas provas objetivas, o intervalo P10–P90 passou, entre 2009 e 2023, de 8,3 para 10,6 p.p. em CH, de 10,0 para 8,9 em CN, de 10,8 para 10,1 em LC e de 6,0 para 15,6 em MT. Em MT, a abertura vem das duas pontas: o P10 caiu de 96,4% para 92,3% da mediana, e o P90 subiu de 102,4% para 107,8%. Em CH, o P10 recuou de 95,6% para 94,1%, o que sugere que a cauda inferior se afastou um pouco mais.

**Interpretação:** não existe uma tendência única de desigualdade territorial para todas as disciplinas. A leitura de longo prazo é de queda da dispersão até 2015–2017, seguida de alta, com pico em 2020 em CH, CN e MT, e de 2022 em LC. Em 2023 CH, CN, LC e Redação ficam abaixo de seus níveis de 2009, com exceção de CH (+8%), mas bem acima das mínimas de 2016. MT é a exceção: o CV continua subindo e é o único em que 2023 supera todos os anos anteriores. A Redação reduziu a dispersão desde 2009, mas continua sendo a mais desigual entre as disciplinas.

**Cautelas:** o número de municípios elegíveis variou de 108 (2016) para 42 (2021) e 58 (2023), e o CV oscila mais quando há menos municípios, em especial em 2020–2021. Parte do aumento desde 2016 pode, portanto, refletir a mudança de composição e não só maior desigualdade real. A confirmação exige o CV calculado sobre um painel fixo de municípios.

O Gini das médias municipais deve ser lido como indicador complementar. Seus valores são baixos porque medem desigualdade relativa entre médias de notas, que têm uma faixa de variação limitada em relação ao nível médio. Ele acompanha o CV quase proporcionalmente (Gini ≈ 0,0055 × CV), então não traz informação independente e não substitui a leitura conjunta de CV e P90–P10.

## **T04 — Quais municípios apresentaram maior evolução do desempenho?**



## Quais municípios apresentaram maior evolução do desempenho?

A comparação foi realizada entre 2009 e 2023, mantendo a mesma estrutura de exame e a mesma escala. Foram considerados os municípios elegíveis nos dois anos, totalizando 48 municípios por disciplina. Para a análise comparativa, também foram considerados os municípios com pelo menos 20 participantes em cada ano.

| Disciplina | Municípios comuns | Variação mediana (pontos) | Variação média (pontos) | Menor variação | Maior variação |
| ---------- | ----------------- | ------------------------- | ----------------------- | -------------- | -------------- |
| CH         | 48                | +30,15                    | +28,76                  | -3,43          | +56,53         |
| CN         | 48                | +9,93                     | +9,15                   | -16,37         | +34,85         |
| LC         | 48                | +30,72                    | +29,75                  | -0,82          | +55,47         |
| MT         | 48                | +20,50                    | +24,40                  | -12,68         | +62,01         |
| Redação    | 48                | +200,51                   | +204,20                 | +112,41        | +318,22        |

A maior evolução mediana em pontos ocorreu na Redação, seguida por LC e CH. Em CN, o ganho mediano foi mais modesto. Apesar da evolução positiva das medianas, foram observadas variações negativas em alguns municípios de CH, CN, LC e MT. Na Redação, todos os municípios comuns apresentaram aumento das médias entre 2009 e 2023.

A comparação das posições relativas dos municípios acrescenta outra dimensão aos resultados. Considerando a variação no ranking (`delta_rank`), destacam-se:

- **CH:** Acará (+20 posições), Tailândia (+18) e Dom Eliseu (+17).

- **CN:** Abaetetuba (+23 posições), Óbidos (+20) e Salinópolis (+14).

- **LC:** Dom Eliseu (+23 posições), Salinópolis (+18) e Redenção (+12).

- **MT:** Dom Eliseu (+17 posições), Tailândia e Cametá (+15 cada).

- **Redação:** Canaã dos Carajás (+38 posições), Tucuruí (+25) e Altamira (+23).

Também foram observadas perdas expressivas de posição relativa. Breves apresentou uma das maiores quedas em CH (-26 posições), CN (-26), LC (-24) e MT (-27). Em Redação, Óbidos teve a maior queda entre os municípios destacados (-29 posições).

**Interpretação:** a evolução do desempenho entre 2009 e 2023 foi positiva na maioria dos municípios, mas não ocorreu de maneira uniforme. A Redação apresentou os maiores ganhos absolutos, tanto na variação mediana quanto na média, enquanto CN registrou os menores ganhos centrais. A análise dos rankings evidencia mudanças na posição relativa dos municípios: alguns avançaram significativamente, como Canaã dos Carajás em Redação e Abaetetuba em CN, enquanto outros perderam posições, como Breves em diferentes disciplinas.

Esses resultados mostram que o aumento das médias não implica necessariamente melhora da posição relativa de um município. Da mesma forma, a mudança no ranking depende do desempenho dos demais municípios e não representa, isoladamente, uma medida de crescimento da nota. Por fim, a comparação descreve a diferença entre dois anos de referência, não permitindo afirmar que a evolução ocorreu continuamente ao longo do período.

## **T05 — Há concentração territorial dos melhores resultados?**

## Há concentração territorial dos melhores resultados?

O ranking anual identifica os municípios que aparecem entre os dez melhores em cada disciplina, considerando apenas os municípios elegíveis. A frequência de aparição no Top 10, expressa como percentual dos anos analisados, permite avaliar a recorrência dos resultados elevados.

Entre 2009 e 2023, Belém apresentou presença no Top 10 em todos os anos nas quatro disciplinas avaliadas (CH, CN, LC e MT). Castanhal também esteve entre os dez primeiros em todos os anos nessas disciplinas. Ananindeua apresentou o mesmo comportamento em CH, CN e LC, com presença em 86,7% dos anos em MT.

Paragominas e Tucuruí também se destacaram pela recorrência, com percentuais elevados nas quatro disciplinas. Canaã dos Carajás apresentou presença especialmente expressiva em CN, LC e MT, enquanto Parauapebas se destacou em MT e LC.

Alguns destaques da frequência no Top 10:

| Disciplina | Município         | Anos no Top 10 (%) |
| ---------- | ----------------- | ------------------ |
| CH         | Belém             | 100,0              |
| CH         | Castanhal         | 100,0              |
| CH         | Ananindeua        | 100,0              |
| CH         | Paragominas       | 86,7               |
| CN         | Belém             | 100,0              |
| CN         | Castanhal         | 100,0              |
| CN         | Ananindeua        | 100,0              |
| CN         | Paragominas       | 80,0               |
| LC         | Belém             | 100,0              |
| LC         | Castanhal         | 100,0              |
| LC         | Ananindeua        | 100,0              |
| LC         | Paragominas       | 93,3               |
| MT         | Belém             | 100,0              |
| MT         | Castanhal         | 100,0              |
| MT         | Parauapebas       | 93,3               |
| MT         | Ananindeua        | 86,7               |
| MT         | Canaã dos Carajás | 85,7               |

Na Redação, considerando a série de 2002 a 2023, Santarém aparece no Top 10 em 95,5% dos anos analisados, seguido por Belém (86,4%) e Castanhal (68,2%). Paragominas também apresenta presença recorrente, com 59,1%. Essa janela histórica mais longa não deve ser comparada diretamente com os percentuais das disciplinas avaliadas entre 2009 e 2023.

**Interpretação:** os melhores resultados municipais apresentam concentração recorrente em um conjunto de municípios, especialmente Belém e Castanhal, que mantêm presença no Top 10 em todos os anos analisados nas quatro disciplinas pós-2009. Ananindeua também apresenta elevada recorrência, enquanto Paragominas se destaca pela presença consistente em diferentes áreas do conhecimento. Na Redação, Santarém assume posição de destaque, com presença no Top 10 em quase toda a série analisada.

A recorrência no Top 10 indica consistência do posicionamento relativo, mas não significa que esses municípios tenham ocupado sempre as primeiras posições ou apresentado desempenho superior em todas as comparações. Além disso, a análise está condicionada ao critério de elegibilidade (N > 100). Assim, municípios com participação reduzida podem não integrar o ranking, mesmo que apresentem médias elevadas. Os resultados descrevem a concentração dos melhores posicionamentos entre os municípios elegíveis, não a distribuição integral do desempenho em todo o território paraense.ar fora da comparação, mesmo que tenham médias elevadas.

## **T06 — Como evoluiu a desigualdade territorial por disciplina?**

## Como evoluiu a desigualdade territorial por disciplina?

A análise de dispersão anual de T06 reproduz os mesmos indicadores apresentados na tabela T03. Assim, T06 deve ser interpretada como uma leitura temporal desses indicadores, e não como uma evidência independente.

A comparação do coeficiente de variação (CV) entre 2009 e 2023 resume os principais movimentos:

| Disciplina | CV em 2009 | CV em 2023 | Síntese              |
| ---------- | ---------- | ---------- | -------------------- |
| CH         | 3,64%      | 3,93%      | Pequena ampliação    |
| CN         | 3,84%      | 3,68%      | Pequena redução      |
| LC         | 4,16%      | 3,84%      | Redução              |
| MT         | 2,50%      | 5,84%      | Ampliação expressiva |
| Redação    | 13,57%     | 9,16%      | Redução relativa     |

A trajetória anual não foi monotônica. Em 2020, o CV aumentou em CH, CN, LC e MT em relação a 2019. Em Matemática, a dispersão já havia apresentado uma elevação expressiva em 2012, quando atingiu 5,06%, e voltou a crescer nos anos finais, chegando a 5,84% em 2023, o maior valor da série. Esse comportamento também é observado no intervalo interquartil (IQR), que passou de 14,91 pontos em 2009 para 37,57 em 2023, indicando maior afastamento entre os valores centrais das distribuições municipais.

Em Ciências Humanas, o CV apresentou redução até 2015, mas voltou a aumentar nos anos seguintes, especialmente em 2020. Em 2023, alcançou 3,93%, ligeiramente acima do valor de 2009. Em Ciências da Natureza e Linguagens, apesar das oscilações anuais, os valores finais ficaram abaixo dos observados no início da série.

Na Redação, o CV diminuiu de 13,57% em 2009 para 9,16% em 2023. Entretanto, essa redução não foi contínua: após atingir valores inferiores a 7% em alguns anos, voltou a crescer entre 2022 e 2023.

**Interpretação:** a desigualdade territorial evoluiu de forma distinta entre as disciplinas. Matemática é o principal ponto de atenção, apresentando ampliação expressiva da dispersão entre as médias municipais, especialmente nos anos finais da série. Ciências Humanas também terminou o período com dispersão ligeiramente superior à inicial. Em contrapartida, Ciências da Natureza e Linguagens apresentaram reduções relativas, enquanto a Redação, apesar de manter um CV superior ao das demais disciplinas, registrou redução expressiva em relação a 2009.

Esses resultados indicam que não houve uma trajetória única de convergência ou divergência territorial no desempenho. A evolução depende da disciplina e do período considerado. Como os indicadores são calculados sobre as médias municipais, eles descrevem a variabilidade entre municípios, não a dispersão das notas individuais dos participantes. Além disso, as diferenças anuais no número de municípios considerados devem ser levadas em conta na interpretação dos resultados..

## **T07 — Existe relação entre participação e desempenho municipal?**

## **T07 — Existe relação entre participação e desempenho municipal?**

As correlações de Pearson, Spearman e Pearson entre o logaritmo do número de participantes e a média municipal foram positivas em todos os anos e disciplinas apresentados. Considerando a mediana anual dos coeficientes entre 2009 e 2023, os resultados foram:

| Disciplina | Pearson (N, média) | Spearman (N, média) | Pearson (log N, média) |
| ---------- | ------------------ | ------------------- | ---------------------- |
| CH         | 0,469              | 0,540               | 0,645                  |
| CN         | 0,461              | 0,520               | 0,628                  |
| LC         | 0,454              | 0,524               | 0,625                  |
| MT         | 0,469              | 0,518               | 0,603                  |
| Redação    | 0,381              | 0,528               | 0,583                  |

Os resultados indicam uma associação positiva entre o número de participantes e a média municipal: municípios com maior participação tendem, em termos gerais, a apresentar médias mais elevadas. Essa associação é mais intensa quando o número de participantes é transformado pelo logaritmo. Em todas as disciplinas, a mediana de Pearson calculada com logaritmo é superior à correlação calculada com o número absoluto de participantes.

A correlação de Spearman também apresenta valores positivos, indicando que a associação não se restringe à relação linear entre as variáveis. Na Redação, por exemplo, a mediana de Spearman (0,528) é superior à de Pearson com o número absoluto de participantes (0,381), enquanto a correlação com logaritmo alcança 0,583.

### Variação temporal da associação

A evolução dos coeficientes anuais mostra que a associação não permanece constante. Em CH, CN, LC e MT, a correlação de Pearson com logaritmo apresenta oscilações ao longo de 2009–2023. Em 2022, por exemplo, os coeficientes atingem valores relativamente elevados: 0,716 em CH, 0,709 em CN, 0,671 em LC e 0,683 em MT. Em 2023, os valores recuam para 0,650, 0,643, 0,625 e 0,665, respectivamente.

Na Redação, a associação também varia. O coeficiente de Pearson com logaritmo passa de 0,372 em 2009 para 0,692 em 2015, recuando para 0,585 em 2023. Portanto, embora a associação seja positiva, sua intensidade apresenta diferenças entre os anos.

Os intervalos de confiança de 95% calculados para Pearson com logaritmo ajudam a representar a incerteza das estimativas. Sua amplitude varia conforme o número de municípios considerados em cada ano, que também não é constante. Nas quatro áreas do conhecimento, por exemplo, a quantidade de municípios varia de 42 a 108 no período analisado.

### Formato da relação: curvas LOWESS

As curvas LOWESS de CH, MT e Redação, apresentadas para 2009, 2016 e 2023, acrescentam uma informação que não aparece diretamente nos coeficientes de correlação: a relação entre participação e média municipal pode apresentar comportamento não linear.

- **CH:** em 2009, a curva apresenta uma pequena queda inicial, seguida de recuperação. Em 2016, predomina uma tendência crescente, com um trecho relativamente estável na região intermediária. Em 2023, a tendência é predominantemente crescente ao longo da faixa observada.

- **MT:** em 2009, observa-se uma curva com formato de U pouco acentuado. Em 2016, esse comportamento fica mais evidente, com redução inicial das médias e posterior recuperação. Em 2023, a curva também apresenta formato de U, com crescimento mais pronunciado na parte superior da distribuição de participantes.

- **Redação:** em 2009, a curva apresenta tendência crescente. Em 2016 e 2023, observa-se uma redução inicial, seguida de recuperação das médias conforme aumenta o número de participantes.

Esses formatos indicam que uma única relação linear pode não representar adequadamente todos os recortes. Entretanto, as curvas correspondem a três anos selecionados e a três disciplinas; não permitem generalizar o mesmo comportamento para todas as áreas ou para todos os anos.

### Interpretação

Existe uma associação positiva entre participação e desempenho médio municipal no Pará. Municípios com maior número de participantes tendem a apresentar médias mais elevadas, e essa associação é mais expressiva quando o número de participantes é considerado em escala logarítmica.

As curvas LOWESS mostram, adicionalmente, que essa relação pode assumir formatos distintos entre disciplinas e anos, incluindo comportamentos curvilíneos. Assim, o aumento da participação não está associado a uma variação uniforme das médias em toda a distribuição municipal.

É importante ressaltar que esses resultados são descritivos. A correlação não demonstra que o aumento do número de participantes provoque melhoria no desempenho. Características demográficas, socioeconômicas, educacionais e territoriais podem estar relacionadas simultaneamente à participação e às médias municipais.

Portanto, a análise reforça a importância de considerar o porte e a cobertura dos municípios na comparação dos resultados do ENEM. As médias municipais devem ser interpretadas levando em conta o número de participantes e a possível não linearidade dessa relação, sem atribuir a ela uma explicação causal.

# ****Conclusões gerais do Eixo 5**

O conjunto dos resultados evidencia desigualdades territoriais no desempenho dos participantes do ENEM no Pará. Essas diferenças se manifestam na evolução das médias municipais, na estabilidade temporal, na dispersão entre municípios e na recorrência dos melhores posicionamentos.

Entre 2009 e 2023, as médias ponderadas estaduais aumentaram nas cinco disciplinas, mas com magnitudes distintas. Redação e Matemática apresentaram as maiores variações entre os extremos, enquanto Ciências da Natureza registrou a menor. Essa evolução, entretanto, não foi linear e não representa necessariamente uma melhoria uniforme entre os municípios, especialmente diante da redução da cobertura municipal elegível nos anos finais.

A análise de estabilidade mostrou que Ciências da Natureza e Linguagens apresentaram menor variação relativa das médias municipais ao longo do período. Redação teve a maior oscilação temporal. Esse resultado não indica, por si só, desempenho inferior, mas evidencia maior variação de suas médias municipais ao longo dos anos.

A dispersão territorial também apresentou comportamentos distintos entre as disciplinas. Matemática se destaca pelo aumento expressivo da dispersão relativa entre 2009 e 2023, tornando-se o principal ponto de atenção nesse aspecto. Ciências Humanas apresentou pequena ampliação, enquanto Ciências da Natureza e Linguagens registraram reduções. Redação também apresentou redução relativa em relação a 2009, embora continue exibindo a maior dispersão entre as médias municipais em 2023.

A comparação dos 48 municípios comuns entre 2009 e 2023 demonstrou que a evolução do desempenho não foi homogênea. Em Ciências Humanas, Ciências da Natureza, Linguagens e Matemática, foram observados municípios com variações negativas entre os dois extremos. Na Redação, todos os municípios comparáveis apresentaram aumento das médias. Portanto, a evolução positiva das médias estaduais não significa avanço uniforme em todo o território.

Os rankings revelam concentração recorrente dos melhores posicionamentos em um conjunto de municípios. Belém e Castanhal estiveram no Top 10 em todos os anos analisados nas quatro disciplinas pós-2009, enquanto Ananindeua também apresentou elevada recorrência. Paragominas, Tucuruí e Parauapebas se destacaram em diferentes áreas. Na Redação, Santarém apresentou presença especialmente frequente entre os dez melhores. Esses resultados, contudo, estão condicionados ao critério de elegibilidade e não representam necessariamente todos os municípios paraenses.

Por fim, foi identificada associação positiva entre o número de participantes e a média municipal. Municípios com maior participação tendem a apresentar médias mais elevadas, e essa associação é mais intensa quando o número de participantes é considerado em escala logarítmica. As curvas LOWESS também indicam que essa relação pode apresentar formatos distintos entre disciplinas e anos. Entretanto, trata-se de uma associação descritiva, que não permite afirmar que o aumento da participação cause melhoria do desempenho.

**Em síntese, o Eixo 5 mostra que o desempenho no ENEM no Pará apresenta diferenças territoriais persistentes, tanto nos níveis das médias quanto em sua evolução e dispersão. Matemática merece atenção pelo aumento da desigualdade relativa entre as médias municipais, enquanto a Redação se destaca pela maior dispersão em 2023 e pela maior oscilação temporal. A recorrência de determinados municípios entre os melhores posicionados evidencia concentração territorial dos resultados mais elevados. Ao mesmo tempo, a evolução positiva das médias estaduais não representa uma trajetória homogênea entre os municípios. Essas conclusões devem ser interpretadas considerando o critério de elegibilidade N > 100, a variação da cobertura municipal e o caráter descritivo das análises.****

## **Observações metodológicas antes de consolidar o eixo**

1. **Escala anterior a 2009:** a planilha mostra `OBJETIVA` e `REDAÇÃO` de 2002–2008 em magnitudes próximas de 0–100. A partir de 2009, as notas aparecem em magnitudes próximas de 0–1000. Não se deve multiplicar os valores automaticamente sem conferir a regra de transformação usada na construção da base; tampouco se deve calcular evolução entre esses dois períodos.
2. **T02 e T04 exportados:** a planilha original de T02 contém apenas Redação e T04 compara 2002 com 2023. Esses resultados não respondem adequadamente à comparação das cinco disciplinas em uma janela de escala homogênea. Por isso, as sínteses deste documento para T02 e T04 foram recalculadas diretamente a partir da base municipal completa, restringindo a análise a 2009–2023.
3. **T03 e T06:** os dois quadros apresentam os mesmos indicadores e observações. Na documentação, T03 responde à diferença/dispersão entre municípios e T06 enfatiza a trajetória temporal desses indicadores.
4. **N > 100:** o critério foi aplicado ao total de participantes do município, obtido do painel municipal. Essa opção evita usar a soma de estratos como substituto do total municipal. Municípios com N igual a 100 não são elegíveis.
5. **Cobertura:** a quantidade de municípios elegíveis varia bastante. Em 2023, apenas 58 municípios atenderam ao critério, embora 141 apareçam na cobertura observada. A análise não representa todos os municípios do Pará em todos os anos.
6. **Período final:** os resultados deste arquivo terminam em 2023. Não há base para estender as conclusões de desempenho municipal a 2024 ou 2025.

**Conclusão metodológica:** o Eixo 5 oferece evidências descritivas relevantes sobre a desigualdade territorial, mas a interpretação histórica deve se concentrar em 2009–2023 para as cinco disciplinas. A comparação 2002–2023 exportada originalmente para T04 não deve ser utilizada. As conclusões devem sempre mencionar o critério N > 100 e a variação da cobertura municipal.
