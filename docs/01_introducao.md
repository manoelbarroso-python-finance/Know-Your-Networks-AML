# 1. Introdução

**Do KYC ao Know Your Networks**
*Investigação de risco individual e AML com Python, Neo4j e inteligência externa*

**Autor:** Manoel Barroso

Processos de Know Your Customer (KYC) e Anti-Money Laundering (AML) tradicionalmente começam pela análise individual de clientes, empresas e transações. Informações cadastrais, listas de sanções, identificação de Pessoas Expostas Politicamente (PEPs), registros corporativos e padrões de movimentação financeira formam parte importante desse processo.
Entretanto, muitos riscos relevantes não aparecem quando uma entidade é analisada de forma isolada.

Uma pessoa sem alerta direto pode estar relacionada a uma empresa controlada por outra entidade de interesse. Contas aparentemente independentes podem compartilhar dispositivos, endereços ou contrapartes. Recursos podem circular por diversas entidades antes de retornar à origem. Estruturas societárias também podem criar diferentes camadas entre uma empresa e seu beneficiário final.

Nesses casos, a pergunta deixa de ser apenas:

> "Quem é este cliente?"

e passa a incluir:

> "Com quem este cliente está conectado e qual é a natureza dessas conexões?"

É a partir dessa mudança de perspectiva que surge a proposta deste projeto: avançar de uma análise centrada apenas no KYC individual para uma abordagem de **Know Your Networks**, combinando inteligência externa, resolução de entidades, análise transacional e bancos de dados em grafo.

---

## 1.1 Proposta e objetivo

Este projeto tem como objetivo construir e avaliar um stack acessível para investigação de risco individual e análise de redes aplicadas a KYC e AML.

A arquitetura desenvolvida combina:

- **Python**, para coleta, tratamento, integração e análise dos dados;
- **Neo4j**, para modelagem e investigação das relações entre pessoas, empresas, contas e outros elementos;
- **Neo4j Graph Data Science (GDS)**, para análise de centralidade e detecção de comunidades;
- **Cypher**, para consultas e identificação de padrões dentro do grafo;
- **OFAC SDN Advanced**, utilizada como fonte pública oficial para screening, aliases e atributos de identidade;
- **técnicas de entity resolution**, destinadas a identificar possíveis correspondências entre registros;
- **dados sintéticos de rede e transações**, utilizados para testar padrões investigativos com ground truth controlado sem expor informações financeiras ou cadastrais de indivíduos reais;
- **GraphRAG**, como camada final de recuperação e síntese de evidências estruturadas em linguagem natural.

O objetivo não é reproduzir integralmente plataformas comerciais de compliance ou afirmar que uma solução construída com ferramentas abertas substitui sistemas institucionais.

A proposta é avaliar, de maneira transparente, até que ponto esse conjunto de ferramentas consegue:

1. identificar possíveis correspondências entre entidades;
2. realizar screening a partir de uma fonte pública oficial estruturada;
3. descobrir exposições diretas e indiretas;
4. representar estruturas societárias e relacionamentos complexos;
5. identificar determinados padrões de rede;
6. priorizar casos para investigação;
7. produzir resultados explicáveis e auditáveis.

---

## 1.2 Hipótese central

A hipótese central do estudo é que a incorporação de informações contextuais e da estrutura de relacionamentos entre entidades pode revelar exposições que não seriam observadas em uma análise exclusivamente nominal, tabular ou individual.

Essa ampliação de contexto, entretanto, também pode aumentar o número de candidatos e falsos positivos. Por isso, o ganho analítico deve ser avaliado conjuntamente com precisão, recall, robustez e capacidade de priorização investigativa.

Em termos simplificados:

**KYC tradicional**

Pessoa → atributos → screening → classificação

**Know Your Networks**

Pessoa → atributos → screening → relacionamentos → rede → contexto investigativo

O Neo4j é tratado como uma camada complementar às análises tradicionais, e não como seu substituto.

Sua contribuição é avaliada como uma camada adicional de investigação, especialmente em situações nas quais o contexto relevante emerge das conexões entre entidades e não apenas das características individuais de cada registro.

---

## 1.3 Perguntas de Pesquisa

O estudo foi estruturado para responder às seguintes perguntas:

### 1.3.1 Entity Resolution

Até que ponto técnicas de normalização e fuzzy matching conseguem reconhecer variações de uma mesma entidade sem produzir uma quantidade excessiva de falsos positivos?

### 1.3.2 Screening

Qual é a diferença entre realizar screening apenas pelo nome e utilizar múltiplos atributos disponíveis sobre uma entidade?

### 1.3.3 Robustez

Como o desempenho do matching se altera quando atributos contextuais estão ausentes, divergentes ou degradados, e quais métricas são mais sensíveis a essa deterioração?

### 1.3.4 Análise relacional

A modelagem em grafo consegue revelar exposições indiretas que não seriam evidentes em uma análise individual?

### 1.3.5 Padrões de rede e transações

A análise em grafo e as regras transacionais conseguem recuperar padrões previamente inseridos em um ambiente sintético controlado, incluindo:

- exposição indireta por estrutura societária;
- compartilhamento de dispositivos;
- compartilhamento de endereços;
- fluxo circular entre contas;
- concentração de recursos seguida de repasse rápido?

### 1.3.6 Comparação metodológica

Que informação incremental surge quando o processo evolui da análise individual e tabular para regras de detecção e análise relacional baseada em grafos?

- análise tabular;
- regras tradicionais;
- análise baseada em grafos;

### 1.3.7 Priorização investigativa

As informações extraídas do grafo podem ajudar a reduzir o universo de casos que precisariam ser analisados manualmente?

### 1.3.8 Síntese e comunicação investigativa

Uma camada GraphRAG consegue recuperar evidências de identidade, screening, relacionamentos e transações e convertê-las em uma síntese rastreável e compreensível para apoio à revisão humana e à comunicação de riscos?

## 1.4 Estrutura do estudo

O trabalho segue uma progressão da identidade individual para o contexto relacional e transacional:

1. preparação e avaliação das fontes de dados;
2. ingestão e estruturação da OFAC SDN;
3. entity resolution e comparação dos métodos de matching;
4. testes de robustez sob degradação dos dados;
5. expansão investigativa com Neo4j e Graph Data Science;
6. detecção de padrões AML em transações sintéticas;
7. integração das evidências por meio de GraphRAG.

Cada etapa é avaliada separadamente antes de ser incorporada à camada seguinte, preservando a distinção entre **sinal, evidência, priorização e decisão**.

---
