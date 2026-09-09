# 9. GraphRAG: síntese investigativa orientada por evidências

## 9.1 Objetivo

A etapa final integra o Neo4j a um modelo de linguagem por meio de uma arquitetura de **Graph Retrieval-Augmented Generation (GraphRAG)**.

O objetivo não é utilizar o LLM para determinar risco de forma autônoma. A proposta é permitir que uma pergunta investigativa em linguagem natural seja convertida em consulta estruturada ao grafo, que as evidências sejam recuperadas diretamente do Neo4j e que esse contexto seja posteriormente organizado em uma síntese rastreável.

O GraphRAG atua, portanto, sobre **evidências previamente estruturadas**, mantendo a decisão final sob responsabilidade humana.

## 9.2 Arquitetura implementada

```text
Pergunta investigativa
        ↓
Text2Cypher Retriever
        ↓
Geração automática de Cypher
        ↓
Consulta ao Neo4j
        ↓
Evidências estruturadas
        ↓
LLM
        ↓
Síntese investigativa
        ↓
Revisão humana
```

A implementação utiliza um `Text2CypherRetriever` para transformar a pergunta investigativa em Cypher e recuperar o contexto diretamente do grafo.

A prova de conceito foi implementada com a biblioteca `neo4j-graphrag`, combinando o `Text2CypherRetriever` com o pipeline `GraphRAG` e um modelo de linguagem para a geração da síntese.

O retriever recebeu o schema relevante do grafo e exemplos de consultas compatíveis com o caso investigativo, limitando o contexto de recuperação às estruturas necessárias para a análise.

As propriedades utilizadas exclusivamente para avaliação, como `ground_truth` e `pattern_id`, não foram disponibilizadas ao mecanismo de recuperação.

Essa separação reduz o risco de vazamento de informação entre a construção do experimento e a geração da resposta.

## 9.3 Caso investigativo

A prova de conceito utilizou `PERSON_005`, entidade sintética que reúne diferentes camadas construídas ao longo do projeto.

Sem utilizar propriedades de `ground_truth` ou `pattern_id`, o GraphRAG recuperou informações de:

- identidade;
- screening;
- relações;
- dispositivos;
- contas;
- comportamento transacional.

### 9.3.1 Evidências recuperadas

| Camada | Evidência recuperada |
|---|---|
| Identidade | `PERSON_005`, Ana Beatriz Alves, México, segmento Alta renda |
| Screening | vínculo com `RISK_003`, referência sintética de risco |
| Dispositivos | associação a `DEVICE_001` e `DEVICE_025`, compartilhados com outras pessoas |
| Conta | propriedade de `ACCOUNT_005`, denominada em USD |
| Transações | quatro entradas em curto intervalo e repasse posterior para `ACCOUNT_105` |

Tanto `PERSON_005` quanto `RISK_003` pertencem ao ambiente sintético do experimento. A eventual referência de origem associada à `RiskEntity` representa apenas o contexto de screening modelado e não corresponde a uma pessoa ou organização real da OFAC.

| Origem | Valor | Horário |
|---|---:|---:|
| `ACCOUNT_020` | USD 2.800 | 09:00 |
| `ACCOUNT_021` | USD 3.100 | 09:18 |
| `ACCOUNT_022` | USD 2.600 | 09:37 |
| `ACCOUNT_023` | USD 3.000 | 09:55 |

Total recebido: **USD 11.500**.

Às 10:35, `ACCOUNT_005` enviou **USD 10.700** para `ACCOUNT_105`, cuja propriedade no grafo está associada a `COMPANY_005`.

Essas evidências correspondem ao comportamento detectado anteriormente pela camada AML transacional, mas foram recuperadas novamente pelo GraphRAG a partir de uma pergunta em linguagem natural.

### 9.3.2 Síntese investigativa produzida

A partir das evidências recuperadas, o GraphRAG produziu uma síntese estruturada do caso em cinco dimensões.

**Evidências observadas**

A resposta identificou `PERSON_005`, sua associação direta a `RISK_003`, sua conta financeira e os dispositivos relacionados.

**Contexto relacional**

Os dispositivos `DEVICE_001` e `DEVICE_025` também aparecem associados a outras pessoas na rede.

Essas conexões foram apresentadas como contexto investigativo, sem interpretar o compartilhamento de dispositivos, isoladamente, como evidência de irregularidade.

**Contexto transacional**

A síntese reconstruiu as quatro entradas totalizando **USD 11.500** e o posterior envio de **USD 10.700** para `ACCOUNT_105`.

**Motivos para revisão**

Foram destacados conjuntamente:

- associação direta a uma referência sintética de risco;
- dispositivos compartilhados;
- concentração de recursos provenientes de múltiplas contrapartes;
- repasse subsequente de parcela relevante dos valores recebidos.

Esses elementos justificam diligência adicional, mas não constituem isoladamente prova de atividade ilícita.

**Limitações**

A resposta também registrou que:

- não é conhecido o motivo econômico das transferências;
- o experimento não contém todo o fundamento subjacente da referência de risco;
- compartilhamento de dispositivos não demonstra, por si só, irregularidade;
- nenhuma informação de `ground_truth` ou `pattern_id` foi utilizada na geração da síntese.

> **O ganho do GraphRAG não está em criar uma nova classificação de risco, mas em reunir evidências dispersas e convertê-las em uma narrativa investigativa rastreável para revisão humana.**

## 9.4 Rastreabilidade da resposta

A execução preserva três artefatos distintos:

1. **consulta Cypher gerada**;
2. **contexto efetivamente retornado pelo Neo4j**;
3. **síntese produzida pelo modelo de linguagem**.

Essa separação permite verificar se uma afirmação presente no relatório possui suporte nas evidências recuperadas.

A rastreabilidade, entretanto, não elimina a necessidade de validação. Uma consulta Cypher gerada incorretamente pode recuperar um contexto incompleto ou inadequado mesmo que a síntese posterior permaneça fiel aos dados retornados.

Por isso, a avaliação deve considerar separadamente:

1. se a consulta gerada representa corretamente a pergunta;
2. se os dados recuperados são suficientes e pertinentes;
3. se a síntese permanece aderente ao contexto recuperado.

Conceitualmente:

```text
pergunta
   ↓
Cypher
   ↓
dados recuperados
   ↓
síntese
```
O modelo também foi instruído a distinguir:

* observação;
* interpretação;
* motivo para revisão;
* limitação.

Essa rastreabilidade reduz o risco de tratar linguagem fluente como evidência autônoma.

## 9.5 Utilidade para gestão de riscos

A principal contribuição do GraphRAG está na capacidade de transformar estruturas técnicas complexas em uma narrativa investigativa mais acessível.

Um analista pode partir de uma pergunta como:

**"Quais evidências disponíveis ajudam a contextualizar esta entidade?"**

Um caso pode exigir a integração simultânea de:

```text
identidade
    +
screening
    +
relações
    +
dispositivos compartilhados
    +
contas
    +
transações
```
O GraphRAG reduz o custo cognitivo de navegar manualmente por essas diferentes camadas ao organizar as evidências em uma narrativa comum.

Essa capacidade pode ser particularmente útil para:

- investigação de casos;
- preparação de relatórios;
- apoio à revisão independente ou por segunda linha;
- comunicação com gestão de riscos;
- discussão em comitês;
- documentação do racional investigativo.

O GraphRAG funciona como uma camada de **recuperação e comunicação assistida**, não como substituto da análise profissional.

## 9.6 Limitações e governança

Uma resposta gerada em linguagem natural não deve ser tratada como prova de atividade ilícita nem como decisão autônoma de compliance.

A utilização responsável exige:

- consultas restritas às fontes autorizadas;
- rastreabilidade das evidências;
- controle de acesso ao grafo;
- validação das consultas produzidas;
- separação entre observação e interpretação;
- proteção de informações sensíveis;
- revisão humana antes de qualquer decisão.

Há também limitações experimentais:

- apenas um caso foi utilizado na prova de conceito;
- o grafo e as transações são sintéticos;
- não foi conduzida avaliação sistemática, sobre um conjunto amplo de perguntas, de factualidade, completude, consultas incorretas ou afirmações sem suporte nas evidências recuperadas;
- o experimento demonstra viabilidade técnica e rastreabilidade, não equivalência a uma ferramenta institucional de investigação.
- a prova de conceito avaliou um único caso investigativo e não permite estimar taxas de erro do GraphRAG;
- o desempenho depende do schema disponibilizado ao retriever, dos exemplos fornecidos, da qualidade do Cypher gerado e do modelo de linguagem utilizado.

Em uma implementação institucional, consultas geradas automaticamente também deveriam estar sujeitas a controles de acesso, validação de schema, logging e políticas adequadas de execução no banco.

Conexões compartilhadas, centralidade elevada, associação comunitária ou padrões transacionais incomuns podem justificar análise adicional, mas nenhum desses elementos constitui isoladamente evidência de irregularidade.

## 9.7 Síntese da etapa GraphRAG

A prova de conceito mostrou que uma pergunta em linguagem natural pode ser convertida em consulta estruturada, recuperar informações distribuídas pelo grafo e produzir uma síntese coerente com as evidências observadas.

O valor principal não está na geração de texto em si, mas na composição de três capacidades:

```text
recuperação estruturada
        +
  rastreabilidade
        +
    comunicação
```
Essas três capacidades possuem funções diferentes: a recuperação conecta a pergunta às informações armazenadas no grafo; a rastreabilidade permite inspecionar o caminho entre consulta e evidência; e a geração em linguagem natural organiza o resultado para consumo humano.

A camada generativa permanece subordinada às evidências recuperadas e à revisão profissional.

O GraphRAG fecha, assim, a arquitetura técnica do projeto ao reunir identidade, screening, estrutura relacional e comportamento transacional em uma interface investigativa comum.

## 9.8 Conclusões gerais e implicações para KYC/AML

O projeto partiu de uma pergunta individual — **quem é esta entidade?** — e progressivamente incorporou novas camadas de evidência até chegar à análise integrada de identidade, relacionamentos e comportamento.

Os resultados permitem sintetizar a contribuição de cada abordagem:

| Camada | Principal resultado | Implicação |
|---|---|---|
| Correspondência exata | baixa tolerância a aliases e variações nominais | regra isolada é excessivamente restritiva |
| Similaridade nominal | Recall elevado, mas baixa capacidade de desambiguação | adequada para geração de candidatos |
| Matching multivariado | F1 ≈ **0,996** no benchmark base | contexto acrescenta forte poder discriminativo |
| Stress testing | degradação contextual reduz principalmente Recall | qualidade do dado é parte do risco do modelo |
| Neo4j | Recall **0,333 → 1,000** com expansão da rede | relações revelam exposições invisíveis ao screening individual |
| Priorização | fila **37 → 17**, preservando Recall **0,833** | expansão relacional precisa ser acompanhada de gestão do ruído |
| Centralidade de grau | maior hub era propositalmente legítimo | importância estrutural não deve ser confundida com risco |
| Louvain | **17 comunidades**, modularidade ≈ **0,705** | comunidades acrescentam contexto estrutural |
| AML transacional | dois padrões controlados recuperados | valida funcionalmente a combinação de estrutura, direção, tempo e valor no ambiente sintético |
| GraphRAG | integração das evidências em síntese rastreável | demonstra potencial para facilitar acesso e comunicação sem substituir julgamento humano |

### Principais conclusões

1. **Identidade não deve depender apenas do nome.**
   Similaridade nominal é útil para encontrar candidatos, mas atributos contextuais são fundamentais para distinguir identidades difíceis.

2. **Qualidade de dados é parte central da eficácia do screening.**
   Quando atributos contextuais se deterioram, o modelo mantém elevada Precisão, mas perde Recall e passa a deixar mais correspondências verdadeiras sem identificação.

3. **Mais contexto também produz mais ruído.**
   A expansão da rede recuperou todas as exposições inseridas no ground truth, mas aumentou significativamente os falsos positivos. O valor do grafo depende, portanto, da capacidade de interpretar e priorizar relações.

4. **Estrutura não equivale a risco.**
   Hubs, comunidades, dispositivos compartilhados e endereços comuns representam sinais relacionais. Sua relevância depende da natureza e do contexto das conexões.

5. **Comportamento acrescenta uma dimensão diferente da identidade.**
   A análise transacional permite observar não apenas quem está conectado, mas como valores circulam entre as entidades ao longo do tempo.

6. **Automação não elimina a necessidade de governança.**
   Scores, regras, grafos e LLMs produzem sinais e evidências. A decisão de compliance permanece dependente de contexto, documentação, controles e revisão humana.

7. **Rastreabilidade não elimina risco de modelo.**
   Mesmo quando a resposta final pode ser ligada às evidências recuperadas, erros podem ocorrer na geração da consulta, na seleção do contexto ou na interpretação. Controles e validação permanecem necessários em todas as camadas.

### Relevância para sistemas de KYC e AML

Em ambientes de KYC e AML, o desafio raramente está em uma única técnica. O problema é combinar informações incompletas, **múltiplos tipos de evidência**, relações indiretas e grandes volumes de candidatos sem transformar cada sinal em alerta conclusivo.

A abordagem avaliada sugere uma arquitetura em camadas:

```text
identidade
    ↓
screening
    ↓
contexto
    ↓
rede
    ↓
comportamento
    ↓
priorização
    ↓
síntese
    ↓
revisão humana
```
Essa arquitetura permite separar sinal, evidência, prioridade e decisão, preservando rastreabilidade ao longo do processo.

Os resultados não validam um sistema produtivo universal de KYC/AML. Eles demonstram, em ambiente controlado e reproduzível, que a integração entre entity resolution, testes de robustez, análise de grafos, Graph Data Science, regras transacionais e GraphRAG pode ampliar a capacidade investigativa sem abandonar os princípios de explicabilidade e governança.

> **A principal contribuição do projeto não está em uma ferramenta isolada, mas em demonstrar, de forma controlada e mensurável, como métodos complementares podem ser organizados para transformar dados fragmentados em contexto investigativo rastreável, mantendo a decisão final sob responsabilidade humana.**
