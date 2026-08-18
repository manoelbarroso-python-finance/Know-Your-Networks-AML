# Arquitetura do projeto

## 1. Visão geral

O projeto será construído como um pipeline investigativo modular.

Em vez de utilizar uma única ferramenta para tentar resolver todo o problema de KYC e AML, cada componente terá uma responsabilidade específica.

A arquitetura foi desenhada para separar:

- coleta de inteligência externa;
- preparação e padronização dos dados;
- resolução de entidades;
- screening;
- construção da rede;
- investigação em grafo;
- análise quantitativa;
- avaliação da eficácia;
- revisão e interpretação dos resultados.

Essa separação é importante porque problemas diferentes exigem ferramentas diferentes.

Um banco de dados em grafo, por exemplo, pode ser extremamente eficiente para investigar relacionamentos, mas não substitui processos de limpeza de dados, matching de identidade ou validação de resultados.

---

## 2. Arquitetura conceitual

O fluxo principal do projeto será:

```text
                    FONTES EXTERNAS
         sanções | PEP | empresas | registros
                          │
                          ▼
                     INGESTÃO
                        Python
                          │
                          ▼
               LIMPEZA E PADRONIZAÇÃO
        nomes | datas | países | identificadores
                          │
                          ▼
                 ENTITY RESOLUTION
      exact match | fuzzy match | atributos auxiliares
                          │
                          ▼
                      SCREENING
             possíveis correspondências
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
      DADOS CORPORATIVOS       BASE SEMISSINTÉTICA
      relações societárias    clientes | contas |
      e identificadores       transações | devices
              │                       │
              └───────────┬───────────┘
                          ▼
                        NEO4J
            entidades + relacionamentos
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
        REGRAS CYPHER           GRAPH ANALYTICS
        caminhos                centralidade
        exposição               comunidades
        ciclos                  conectividade
        relações                estrutura da rede
             │                         │
             └────────────┬────────────┘
                          ▼
                  ANÁLISE EM PYTHON
        métricas | comparação | validação
                          │
                          ▼
                RESULTADO INVESTIGATIVO
       evidências | sinais | limitações |
                necessidade de revisão

## Camada experimental de GraphRAG e geração assistida por LLM

Uma extensão prevista para as etapas finais do projeto será avaliar o uso de Graph Retrieval-Augmented Generation (GraphRAG).

A proposta não será utilizar um Large Language Model (LLM) para substituir as regras de screening, os algoritmos de grafo ou a revisão humana.

O objetivo será avaliar se um modelo generativo consegue utilizar o contexto estruturado recuperado do Neo4j para produzir relatórios investigativos mais completos, rastreáveis e consistentes.

A arquitetura conceitual será:

```text
Neo4j
  │
  ├── entidades
  ├── relacionamentos
  ├── caminhos
  ├── sinais
  └── evidências
          │
          ▼
       GraphRAG
 recuperação contextual
          │
          ▼
          LLM
          │
          ▼
 Relatório investigativo
