# 3. Fontes de dados e definição do escopo

## 3.1 Objetivo

A qualidade de processos de KYC, screening e investigação financeira depende não apenas dos métodos analíticos utilizados, mas também da qualidade, cobertura, atualidade e rastreabilidade das informações consultadas.

Durante o desenho do projeto foram avaliadas diferentes fontes públicas e especializadas. Entretanto, a implementação final adotou um escopo deliberadamente controlado, baseado principalmente em:

- **OFAC SDN Advanced**, como fonte externa oficial para sanções, aliases, atributos de identidade e documentos;
- **dados derivados da própria OFAC**, utilizados na construção dos benchmarks de entity resolution;
- **dados sintéticos**, utilizados para os experimentos de rede e comportamento transacional.

A redução do número de fontes foi uma decisão metodológica. O objetivo principal passou a ser avaliar com profundidade as diferentes camadas analíticas do pipeline, evitando atribuir ganhos de desempenho à simples acumulação de bases externas.

## 3.2 Critérios para seleção das fontes

As fontes foram avaliadas segundo os seguintes critérios:

1. **autoridade e proveniência** da informação;
2. **cobertura** e qualidade dos registros;
3. disponibilidade de **aliases e identificadores auxiliares**;
4. acesso por arquivo estruturado ou API;
5. utilidade para **entity resolution** e screening;
6. capacidade de integração ao pipeline;
7. reprodutibilidade;
8. custo e complexidade proporcionais ao benefício esperado.

A inclusão de uma nova fonte foi condicionada a uma pergunta objetiva:

> **Que informação adicional essa fonte fornece e como esse ganho pode ser medido?**

Esse princípio foi utilizado para limitar o escopo final do estudo.

## 3.3 Fontes avaliadas e escopo final

Durante o planejamento foram consideradas diferentes fontes capazes de ampliar cobertura, contexto regulatório ou relações corporativas.

| Fonte | Avaliada | Implementada | Papel no estudo final |
|---|---:|---:|---|
| OFAC SDN Advanced | Sim | **Sim** | Fonte oficial de sanções, aliases, identidade e documentos |
| OpenSanctions | Sim | Não | Extensão futura para agregação e matching externo |
| ONU Consolidated List | Sim | Não | Extensão futura para diversidade jurisdicional |
| PEP — Portal da Transparência | Sim | Não | Possível camada futura de contexto brasileiro |
| CEIS/CNEP | Sim | Não | Possível camada futura de integridade e terceiros |
| GLEIF | Sim | Não | Possível enriquecimento corporativo |
| GDELT / mídia adversa | Sim | Não | Possível camada futura de contexto aberto |
| Dados sintéticos | — | **Sim** | Rede, ground truth e transações controladas |

A tabela distingue explicitamente **fontes consideradas** de **fontes efetivamente utilizadas**.

A decisão de não incorporar todas as fontes avaliadas evita que o experimento confunda o efeito dos métodos analíticos com o aumento indiscriminado de informação disponível.

## 3.4 Fonte externa implementada: OFAC SDN Advanced

A principal fonte externa utilizada foi a **Specially Designated Nationals and Blocked Persons List (SDN)** da Office of Foreign Assets Control (OFAC), em sua versão estruturada `SDN_ADVANCED.XML`.

A escolha da OFAC oferece três vantagens para o experimento:

1. **autoridade da fonte**, por se tratar da publicação oficial do órgão responsável;
2. riqueza estrutural, incluindo nomes, aliases, atributos de identidade e documentos;
3. possibilidade de construir benchmarks controlados de entity resolution a partir de diferentes representações associadas ao mesmo registro.

A lista não é tratada como uma classificação genérica de risco. Ela funciona como uma **referência oficial de screening** dentro do escopo específico do experimento.

### 3.4.1 Uso em entity resolution

Aliases e diferentes nomes associados à mesma entidade foram utilizados para construir **pares positivos derivados da própria fonte oficial**.

Esses pares representam diferentes formas nominais vinculadas ao mesmo identificador OFAC e funcionam como ground truth intrafonte para o benchmark de entity resolution.

Essa estratégia permite avaliar se diferentes representações de um mesmo registro oficial continuam sendo reconhecidas após normalização e matching.

Os pares negativos foram construídos separadamente, incluindo **hard negatives** com elevada similaridade nominal, evitando que o benchmark fosse artificialmente fácil.

Dessa forma, a OFAC desempenha dois papéis distintos:

```text
Fonte oficial
     ↓
Screening

e

Registros + aliases
     ↓
Benchmark de entity resolution
```

## 3.5 Dados sintéticos e ground truth controlado

Dados sintéticos foram utilizados nas etapas em que informações reais de clientes, contas e transações não seriam apropriadas para publicação.

Foram construídos artificialmente:

- pessoas;
- empresas;
- contas;
- dispositivos;
- endereços;
- entidades de risco;
- relacionamentos entre essas entidades;
- transações financeiras.

As entidades de risco utilizadas nesses experimentos também são sintéticas. Eventuais referências à OFAC representam apenas a categoria ou origem conceitual do sinal de screening e não correspondem a pessoas ou organizações reais inseridas em cenários AML fictícios.

A geração controlada permitiu inserir previamente padrões conhecidos de exposição e comportamento transacional.

Esse ground truth tornou possível avaliar objetivamente se as consultas e regras recuperavam os padrões esperados, sem utilizar informações financeiras ou cadastrais de indivíduos reais.

O ground truth foi mantido separado dos mecanismos de detecção. Ele é utilizado para **avaliar o resultado**, e não para orientar onde o algoritmo deve procurar.


## 3.6 Proveniência e rastreabilidade

O pipeline preserva metadados capazes de identificar a origem e o momento de obtenção dos registros. A implementação inclui uma estrutura específica de proveniência com timestamp em UTC.

Em conjunto com a organização dos scripts e dos artefatos intermediários, essa estrutura permite rastrear:

1. de qual fonte determinado registro foi obtido;
2. quando a coleta foi realizada;
3. qual arquivo ou dataset originou o dado;
4. em qual etapa do pipeline determinado artefato foi produzido.

Essa rastreabilidade é particularmente relevante em contextos de compliance, nos quais resultado analítico, transformação metodológica e evidência de origem devem permanecer distinguíveis.

## 3.7 Separação entre dados brutos, processados e públicos

A estrutura do projeto separa diferentes estágios dos dados:

```text
data/
├── raw/
│   └── dados originais obtidos das fontes
│
├── processed/
│   ├── private/
│   │   └── resultados derivados que não devem ser publicados
│   │
│   └── public/
│       └── artefatos adequados ao repositório público
│
└── synthetic/
    └── entidades, relações e transações artificiais
```

## 3.8 Separação entre fonte, sinal, evidência e decisão

A arquitetura preserva uma distinção fundamental entre a origem da informação e sua interpretação investigativa.

A presença de um registro em uma fonte oficial pode gerar um **sinal de screening**, mas esse sinal não deve ser automaticamente transformado em uma conclusão sobre risco ou irregularidade.

Da mesma forma, conexões observadas no grafo e padrões identificados nas transações constituem elementos de análise cujo significado depende do contexto.

O fluxo conceitual utilizado no projeto é:

```text
fonte
  ↓
dado observado
  ↓
match ou relacionamento
  ↓
sinal
  ↓
contexto
  ↓
priorização
  ↓
revisão humana
  ↓
decisão
```

## 3.9 Limitações do escopo de dados

A utilização predominante de uma única fonte externa oficial impõe limitações importantes.

Entre elas:

- concentração do screening em uma fonte de sanções específica;
- ausência de validação externa com múltiplas jurisdições;
- cobertura incompleta de atributos para determinados tipos de entidade;
- ausência, nesta versão, de dados reais de clientes e transações;
- dependência de dados sintéticos para avaliar padrões relacionais e comportamentais;
- impossibilidade de inferir desempenho operacional em ambiente produtivo apenas a partir dos benchmarks controlados.
- benchmark de entity resolution construído a partir de diferentes representações pertencentes à própria OFAC, sem base independente de onboarding;

Essas limitações são deliberadamente preservadas na interpretação dos resultados.

O objetivo do projeto não é demonstrar cobertura universal de KYC/AML, mas avaliar de forma transparente **como diferentes métodos acrescentam ou perdem informação ao longo do pipeline**.

## 3.10 Síntese da camada de dados

O escopo final combina uma fonte externa oficial e dados experimentais controlados:

```text
OFAC SDN Advanced
        ↓
ingestão e estruturação
        ↓
identidade e screening
        ↓
benchmark de matching

Dados sintéticos
        ↓
rede e transações
        ↓
experimentos Neo4j / AML
```
