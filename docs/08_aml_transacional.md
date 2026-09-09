# 8. AML Transacional: padrões comportamentais em rede

## 8.1 Objetivo

Após a análise de identidade e das relações entre entidades, o projeto acrescenta uma camada transacional sintética para avaliar se o grafo também consegue recuperar **padrões de movimentação previamente definidos para investigação AML**.

O objetivo não é construir um sistema universal de detecção de lavagem de dinheiro, mas testar se **relações transacionais com dimensão temporal** podem ser integradas à mesma estrutura utilizada anteriormente para identidade, screening e análise de rede.

Foram geradas **458 transações sintéticas**:

| Tipo | Transações |
|---|---:|
| Movimentação de fundo | **450** |
| Ground truth controlado | **8** |
| **Total** | **458** |

As oito transações pertencentes ao ground truth foram distribuídas em dois padrões:

1. **fluxo circular entre contas**;
2. **concentração de recursos seguida de repasse rápido**.

O ground truth foi utilizado somente para **avaliar os resultados após a detecção**. As regras responsáveis por localizar os padrões não consultaram os campos utilizados para identificar previamente esses casos.

## 8.2 Construção da camada transacional

As transações foram criadas sobre as contas já existentes na rede sintética.

A maior parte das operações corresponde a **transações de fundo**, destinadas a inserir atividade transacional adicional ao redor dos casos controlados e evitar que os padrões de interesse apareçam completamente isolados no dataset.

As transações de fundo não representam uma estimativa de comportamento bancário real. Sua função é apenas acrescentar complexidade ao ambiente sintético de detecção.

Sobre essa base foram inseridos dois cenários controlados.

A construção sintética oferece duas vantagens metodológicas:

- permite conhecer exatamente quais estruturas deveriam ser recuperadas;
- evita a utilização de transações financeiras pertencentes a indivíduos reais.

Os padrões utilizados representam **tipologias experimentais simplificadas**, e não regras regulatórias completas ou evidência automática de atividade ilícita.

## 8.3 Representação no Neo4j

As transações foram modeladas como relacionamentos entre contas:

```text
(:Account)-[:TRANSFERRED_TO]->(:Account)
```
Cada relacionamento transacional preserva informações como:

1. identificador da transação;
2. valor;
3. moeda;
4. timestamp.

Conceitualmente:
```text
ACCOUNT_A
    │
    │ TRANSFERRED_TO
    │ amount
    │ timestamp
    │ currency
    ▼
ACCOUNT_B
```
Essa modelagem permite consultar simultaneamente a direção do fluxo, o valor transferido e a ordem temporal das operações.

Os timestamps foram estruturados em formato compatível com o tipo datetime do Neo4j antes da carga.

---

## 8.4 Padrão 1 — Fluxo circular

O primeiro cenário representa recursos que atravessam contas intermediárias e retornam à conta de origem.

Em 15 de julho de 2026, foi inserida a seguinte sequência:

| Origem | Destino | Valor | Horário |
|---|---|---:|---:|
| `ACCOUNT_010` | `ACCOUNT_011` | USD 8.500 | 10:00 |
| `ACCOUNT_011` | `ACCOUNT_012` | USD 8.300 | 11:20 |
| `ACCOUNT_012` | `ACCOUNT_010` | USD 8.100 | 13:00 |

A estrutura pode ser representada como:

```text
ACCOUNT_010
    │
    │ USD 8.500
    ▼
ACCOUNT_011
    │
    │ USD 8.300
    ▼
ACCOUNT_012
    │
    │ USD 8.100
    └──────────────► ACCOUNT_010
```
O elemento investigativo relevante não é uma transferência isolada, mas a sequência ordenada de operações que fecha um ciclo entre as contas.

Diferenças entre os valores transferidos foram mantidas deliberadamente, evitando definir circularidade como simples repetição exata do mesmo montante.

## 8.5 Padrão 2 — Concentração e repasse rápido

O segundo cenário combina múltiplas entradas em curto intervalo com uma transferência subsequente de parcela relevante dos recursos acumulados.

Em 20 de julho de 2026, `ACCOUNT_005` recebeu:

| Origem | Valor | Horário |
|---|---:|---:|
| `ACCOUNT_020` | USD 2.800 | 09:00 |
| `ACCOUNT_021` | USD 3.100 | 09:18 |
| `ACCOUNT_022` | USD 2.600 | 09:37 |
| `ACCOUNT_023` | USD 3.000 | 09:55 |

O total recebido foi de:

**USD 11.500**

Posteriormente:

| Origem | Destino | Valor | Horário |
|---|---|---:|---:|
| `ACCOUNT_005` | `ACCOUNT_105` | USD 10.700 | 10:35 |

O padrão pode ser resumido como:

```text
ACCOUNT_020 ─┐
ACCOUNT_021 ─┤
ACCOUNT_022 ─┼──► ACCOUNT_005 ───► ACCOUNT_105
ACCOUNT_023 ─┘
                    │
              recebe 11.500
                    │
              envia 10.700
```
A combinação entre múltiplas origens, concentração temporal e repasse subsequente constitui o padrão avaliado.

Nenhum desses elementos, isoladamente, é tratado como prova de atividade ilícita.

Os dois cenários foram selecionados como **padrões experimentais de comportamento**, e não como representação exaustiva de tipologias AML. Em aplicação real, estruturas semelhantes podem decorrer de atividades legítimas e exigem contexto econômico, perfil do cliente e demais evidências antes de qualquer conclusão.

## 8.6 Estratégia de detecção

As regras foram desenvolvidas para identificar as características estruturais e temporais dos dois padrões sem consultar sua identificação prévia no dataset.

### 8.6.1 Fluxo circular

A detecção procura ciclos entre três contas distintas que:

1. formam a sequência `A → B → C → A`;
2. respeitam a ordem temporal das três transferências;
3. são concluídos dentro de uma janela máxima de seis horas;
4. apresentam valor mínimo de USD 5.000 em cada operação;
5. preservam pelo menos 80% do valor da transferência anterior a cada novo movimento.

### 8.6.2 Concentração e repasse

A segunda regra procura contas que:

1. recebem recursos de pelo menos quatro remetentes distintos em uma janela de até duas horas;
2. acumulam pelo menos USD 9.000 nesse intervalo;
3. realizam uma saída em até uma hora após a última entrada;
4. repassam nessa operação pelo menos 80% do valor concentrado.

### 8.6.3 Parâmetros das regras

As duas regras foram implementadas com critérios explícitos de estrutura, temporalidade e valor. Esses parâmetros permitem reproduzir os padrões avaliados no experimento e evitam que a identificação dependa apenas de inspeção visual das transações.

#### Fluxo circular

A regra procura ciclos formados por três contas distintas:

```text
A → B → C → A
```
Para que um ciclo seja considerado candidato, são exigidos simultaneamente:

| Critério | Parâmetro utilizado |
|---|---|
| Contas distintas | **3** |
| Transferências no ciclo | **3** |
| Ordem temporal | `t1 < t2 < t3` |
| Duração máxima do ciclo | **6 horas** |
| Valor mínimo de cada transferência | **USD 5.000** |
| Valor mínimo da segunda transferência | **80% de t1** |
| Valor mínimo da terceira transferência | **80% de t2** |

A condição de preservação parcial do valor impede que qualquer ciclo nominal entre contas seja automaticamente considerado relevante. Além de retornar à conta de origem, o fluxo precisa manter parcela significativa dos recursos ao longo das transferências.

#### Concentração e repasse rápido

A segunda regra identifica uma conta que recebe recursos de múltiplas origens em curto intervalo e posteriormente repassa parcela relevante do montante concentrado.

Os critérios implementados são:

| Critério | Parâmetro utilizado |
|---|---|
| Remetentes distintos | **mínimo de 4** |
| Janela de concentração das entradas | **até 2 horas** |
| Valor total mínimo recebido | **USD 9.000** |
| Repasse após a última entrada | **até 1 hora** |
| Valor mínimo repassado | **80% do total recebido na janela** |

A janela de duas horas é construída a partir das entradas recebidas pela conta analisada. Após identificar pelo menos quatro remetentes distintos e valor agregado mínimo de **USD 9.000**, a regra procura transferências realizadas após a última entrada e dentro da hora seguinte.

Entre as saídas que satisfazem o critério mínimo de **80% do valor concentrado**, é considerada a primeira operação em ordem temporal.

Esses parâmetros foram definidos para o **experimento sintético**. Eles não representam thresholds regulatórios, limites de monitoramento recomendados ou critérios calibrados sobre comportamento financeiro real.

## 8.7 Resultados

Os dois padrões inseridos foram recuperados pelas regras correspondentes.

| Padrão | Candidatos detectados | Ground truth recuperado |
|---|---:|---:|
| Fluxo circular | **1** | **Sim** |
| Concentração + repasse rápido | **1** | **Sim** |

A ausência de candidatos adicionais neste conjunto controlado não deve ser interpretada como estimativa de Precisão de 100% em ambiente real. Com apenas um caso inserido por padrão e um dataset sintético de pequena escala, o resultado demonstra **recuperação funcional dos cenários conhecidos**, não desempenho estatístico generalizável.

### 8.7.1 Fluxo circular

A consulta identificou a sequência:

```text
ACCOUNT_010
    ↓
ACCOUNT_011
    ↓
ACCOUNT_012
    ↓
ACCOUNT_010
```
correspondente ao ciclo inserido previamente no conjunto sintético.

### 8.7.2 Concentração e repasse

A segunda regra identificou ACCOUNT_005 como conta central do padrão:

* 4 contrapartes de origem;
* USD 11.500 recebidos;
* USD 10.700 enviados posteriormente;
* destino: ACCOUNT_105.

O caso detectado corresponde ao padrão inserido no ground truth.

## 8.8 Interpretação e limitações

Os resultados mostram que, **no ambiente controlado construído**, o Neo4j permitiu representar e consultar simultaneamente **estrutura, direção e temporalidade** das transferências.

O ganho em relação à análise puramente relacional do capítulo anterior é a introdução de uma nova dimensão:

```text
estrutura da rede
        +
direção dos fluxos
        +
      tempo
        +
      valor
```
Entretanto, os resultados possuem limitações importantes:

- apenas duas tipologias foram testadas;
- existe apenas um caso controlado de cada padrão;
- as 458 transações foram geradas sinteticamente;
- os thresholds e janelas temporais não foram calibrados sobre comportamento bancário real;
- não foram avaliadas taxas de falsos positivos em escala operacional;
- uma estrutura transacional compatível com determinada regra não demonstra, isoladamente, intenção ou  atividade ilícita.
- as transações de fundo não foram calibradas para reproduzir distribuições, sazonalidade ou comportamento financeiro observados em uma instituição real;

Portanto, a recuperação dos dois casos deve ser interpretada como **validação funcional das regras no ambiente sintético**, e não como evidência de eficácia produtiva de um sistema AML.

## 8.9 Síntese

A camada transacional amplia progressivamente o contexto investigativo desenvolvido ao longo do projeto:

```text
identidade
    ↓
screening
    ↓
relacionamentos
    ↓
estrutura de rede
    ↓
transações
```
Os dois padrões controlados foram recuperados sem utilização do ground truth durante a detecção, demonstrando que relações financeiras podem ser analisadas dentro da mesma arquitetura de grafo utilizada para identidade e exposição relacional.

Entretanto, à medida que as camadas se acumulam, cresce também a quantidade de informação que um analista precisa reunir e interpretar:

1. **quem é a entidade?** <br> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+
2. **com quem está conectada?** <br> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+
3. **qual referência de risco está presente?** <br> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+
4. **quais contas controla?** <br> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+
5. **como os recursos circularam?**

O capítulo seguinte avalia uma camada de **GraphRAG** destinada justamente a recuperar essas evidências distribuídas e organizá-las em uma síntese investigativa rastreável para revisão humana.
