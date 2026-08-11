# Do KYC ao Know Your Networks

## Investigação de risco individual e AML com Python, Neo4j e inteligência externa

## 1. Introdução

Processos de Know Your Customer (KYC) e Anti-Money Laundering (AML) tradicionalmente começam pela análise individual de clientes, empresas e transações. Informações cadastrais, listas de sanções, identificação de Pessoas Expostas Politicamente (PEPs), registros corporativos e padrões de movimentação financeira formam parte importante desse processo.

Entretanto, muitos riscos relevantes não aparecem quando uma entidade é analisada de forma isolada.

Uma pessoa sem alerta direto pode estar relacionada a uma empresa controlada por outra entidade de interesse. Contas aparentemente independentes podem compartilhar dispositivos, endereços ou contrapartes. Recursos podem circular por diversas entidades antes de retornar à origem. Estruturas societárias também podem criar diferentes camadas entre uma empresa e seu beneficiário final.

Nesses casos, a pergunta deixa de ser apenas:

> "Quem é este cliente?"

e passa a incluir:

> "Com quem este cliente está conectado e qual é a natureza dessas conexões?"

É a partir dessa mudança de perspectiva que surge a proposta deste projeto: avançar de uma análise centrada apenas no KYC individual para uma abordagem de **Know Your Networks**, combinando inteligência externa, resolução de entidades, análise transacional e bancos de dados em grafo.

---

## 2. Proposta do projeto

Este projeto tem como objetivo construir e avaliar um stack acessível para investigação de risco individual e análise de redes aplicadas a KYC e AML.

A arquitetura será baseada principalmente em:

- **Python**, para coleta, tratamento, integração e análise dos dados;
- **Neo4j**, para modelagem e investigação das relações entre pessoas, empresas, contas e outros elementos;
- **Cypher**, para consultas e identificação de padrões dentro do grafo;
- **fontes públicas de inteligência externa**, utilizadas para screening e enriquecimento;
- **técnicas de entity resolution**, destinadas a identificar possíveis correspondências entre registros;
- **dados transacionais sintéticos ou semissintéticos**, utilizados para testar padrões investigativos sem expor informações financeiras de indivíduos reais.

O objetivo não é reproduzir integralmente plataformas comerciais de compliance ou afirmar que uma solução construída com ferramentas abertas substitui sistemas institucionais.

A proposta é avaliar, de maneira transparente, até que ponto esse conjunto de ferramentas consegue:

1. identificar possíveis correspondências entre entidades;
2. realizar screening contra fontes públicas;
3. descobrir exposições diretas e indiretas;
4. representar estruturas societárias e relacionamentos complexos;
5. identificar determinados padrões de rede;
6. priorizar casos para investigação;
7. produzir resultados explicáveis e auditáveis.

---

## 3. Hipótese central

A hipótese que orienta o trabalho é que a incorporação da estrutura de relacionamentos entre entidades pode revelar informações que não seriam observadas em uma análise exclusivamente tabular ou individual.

Em termos simplificados:

**KYC tradicional**

Pessoa → atributos → screening → classificação

**Know Your Networks**

Pessoa → atributos → screening → relacionamentos → rede → contexto investigativo

O Neo4j não será tratado como um substituto das análises tradicionais.

Sua contribuição será avaliada como uma camada adicional de investigação, especialmente em situações nas quais o risco pode surgir das conexões entre entidades e não apenas das características individuais de cada registro.

---

## 4. Perguntas que o projeto pretende responder

Ao final da análise, o projeto buscará responder às seguintes perguntas:

### 4.1 Entity Resolution

Até que ponto técnicas de normalização e fuzzy matching conseguem reconhecer variações de uma mesma entidade sem produzir uma quantidade excessiva de falsos positivos?

### 4.2 Screening

Qual é a diferença entre realizar screening apenas pelo nome e utilizar múltiplos atributos disponíveis sobre uma entidade?

### 4.3 Relacionamentos

A modelagem em grafo consegue revelar exposições indiretas que não seriam evidentes em uma análise individual?

### 4.4 Tipologias de rede

O Neo4j consegue identificar padrões previamente inseridos em uma rede controlada, como:

- concentração de recursos;
- distribuição para múltiplas contrapartes;
- circularidade;
- compartilhamento de dispositivos ou endereços;
- exposição indireta a entidades previamente sinalizadas?

### 4.5 Comparação metodológica

Que informação adicional é obtida ao comparar:

- análise tabular;
- regras tradicionais;
- análise baseada em grafos?

### 4.6 Priorização investigativa

As informações extraídas do grafo podem ajudar a reduzir o universo de casos que precisariam ser analisados manualmente?

---

## 5. Arquitetura conceitual

O fluxo principal será estruturado da seguinte maneira:

```text
FONTES PÚBLICAS
sanções | PEP | empresas | registros externos
                │
                ▼
             PYTHON
coleta | limpeza | normalização | integração
                │
                ▼
       ENTITY RESOLUTION
nomes | aliases | datas | documentos | atributos
                │
                ▼
         BASE SEMISSINTÉTICA
pessoas | empresas | contas | transações | dispositivos
                │
                ▼
              NEO4J
nós | relacionamentos | caminhos | comunidades
                │
        ┌───────┴────────┐
        ▼                ▼
 REGRAS CYPHER      GRAPH ANALYTICS
        │                │
        └───────┬────────┘
                ▼
       ANÁLISE EM PYTHON
métricas | comparação | priorização | validação
                │
                ▼
       RESULTADO INVESTIGATIVO
evidências | contexto | limitações | revisão humana
