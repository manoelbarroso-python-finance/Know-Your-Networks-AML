# 2. Arquitetura do projeto

## 2.1 Visão geral

O projeto foi estruturado como um **pipeline investigativo modular**, no qual cada componente responde a uma função específica do processo de KYC e AML.

Em vez de utilizar uma única ferramenta para resolver todas as etapas, a arquitetura separa aquisição e preparação dos dados, resolução de entidades, screening, análise relacional, avaliação de robustez, investigação transacional e síntese das evidências.

Essa separação permite avaliar cada camada individualmente antes de incorporá-la às etapas seguintes.

A arquitetura separa:

- ingestão e preparação das fontes;
- normalização e padronização;
- resolução de entidades e screening;
- construção de benchmarks e avaliação quantitativa;
- testes de robustez;
- construção e investigação da rede;
- análise estrutural com Graph Data Science;
- detecção de padrões transacionais;
- recuperação e síntese de evidências com GraphRAG;
- revisão e interpretação humana.

Essa separação é importante porque problemas diferentes exigem ferramentas diferentes.

Um banco de dados em grafo, por exemplo, pode ser extremamente eficiente para investigar relacionamentos, mas não substitui processos de limpeza de dados, matching de identidade ou validação de resultados.
Da mesma forma, um modelo de linguagem não substitui regras de detecção ou decisão de compliance: sua função, neste projeto, é organizar e comunicar evidências previamente recuperadas de fontes estruturadas.

---

## 2.2 Arquitetura implementada

O fluxo principal implementado no projeto é:

```text
  OFAC SDN ADVANCED
                    fonte pública oficial
                              │
                              ▼
                     INGESTÃO E PARSING
                           Python
                              │
                              ▼
                 NORMALIZAÇÃO E ESTRUTURAÇÃO
            nomes | aliases | datas | documentos
                              │
                              ▼
                     ENTITY RESOLUTION
           Correspondência exata | RapidFuzz | Multivariado
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
        AVALIAÇÃO DE MATCHING         TESTES DE ROBUSTEZ
   Precisão | Recall | F1 | AP     ausência | divergência
                │                           │
                └─────────────┬─────────────┘
                              ▼
                    REDE SINTÉTICA CONTROLADA
          pessoas | empresas | contas | dispositivos |
               endereços | entidades de risco
                              │
                              ▼
                            NEO4J
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
        CYPHER / REDE        GDS          AML TRANSACIONAL
     caminhos e exposição   Degree          ciclos
        direta/indireta     Louvain      concentração + repasse
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
                           GraphRAG
                   Text2Cypher + Neo4j
                              │
                              ▼
                     SÍNTESE INVESTIGATIVA
            evidências | contexto | limitações
                              │
                              ▼
                       REVISÃO HUMANA

```
A arquitetura segue uma progressão deliberada. Primeiro, a identidade é tratada e avaliada fora do grafo. Em seguida, relacionamentos e transações são incorporados ao Neo4j para ampliar o contexto investigativo. Por fim, o GraphRAG utiliza somente as evidências estruturadas recuperadas do banco para produzir uma síntese em linguagem natural.

Essa sequência preserva a separação entre **identificação, detecção, contextualização, priorização e decisão**.

## 2.3 Camada experimental de GraphRAG e geração assistida por LLM

A arquitetura incorpora, como última camada experimental, uma prova de conceito de **Graph Retrieval-Augmented Generation (GraphRAG)**.

Foi utilizado um retriever `Text2Cypher`, responsável por converter uma pergunta investigativa em uma consulta Cypher, recuperar evidências diretamente do Neo4j e fornecer esse contexto estruturado ao modelo de linguagem.

O LLM não é utilizado para substituir regras de screening, algoritmos de grafo ou revisão humana. Sua função é transformar evidências recuperadas em uma síntese investigativa mais acessível e rastreável.

O fluxo implementado nesta camada é:

```text
Pergunta em linguagem natural
            │
            ▼
      Text2Cypher Retriever
            │
            ▼
       Consulta Cypher
            │
            ▼
           Neo4j
            │
            ▼
    Evidências recuperadas
            │
            ▼
           LLM
            │
            ▼
   Síntese investigativa
            │
            ▼
      Revisão humana
```

## 2.4 Princípios de governança da arquitetura

A arquitetura foi estruturada para preservar quatro princípios:

1. **separação entre sinal, evidência e decisão** — scores, conexões e padrões funcionam como elementos de análise e priorização, mas não são tratados automaticamente como confirmação de irregularidade;
2. **rastreabilidade** — resultados relevantes podem ser associados aos dados, regras ou caminhos que os produziram;
3. **isolamento do ground truth** — informações utilizadas para avaliação não são disponibilizadas aos mecanismos responsáveis pela detecção;
4. **proteção dos dados** — informações reais derivadas das fontes são mantidas separadas dos artefatos públicos e dos datasets sintéticos utilizados nas demonstrações.

A revisão humana permanece como etapa final do processo investigativo.

## 2.5 Modularidade e reprodutibilidade

Cada camada foi implementada de forma independente, com scripts, arquivos intermediários e resultados próprios. Essa organização permite reproduzir ou substituir componentes sem alterar toda a arquitetura.

A sequência dos experimentos também foi organizada para reduzir o risco de que resultados de etapas posteriores influenciem retrospectivamente a avaliação das etapas anteriores.

O capítulo seguinte apresenta as fontes avaliadas, as fontes efetivamente incorporadas e os critérios utilizados para definir o escopo final dos dados.
