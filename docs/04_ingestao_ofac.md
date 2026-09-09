# 4. Ingestão e estruturação da OFAC

## 4.1 Objetivo

A primeira fonte externa real incorporada ao projeto foi a **Specially Designated Nationals and Blocked Persons List (SDN)**, publicada pela **Office of Foreign Assets Control (OFAC)**.

A escolha teve um objetivo metodológico: estabelecer um baseline diretamente a partir de uma **fonte oficial**, antes da aplicação dos métodos próprios de normalização, entity resolution e avaliação de robustez.

Nesta implementação, a OFAC desempenha três funções principais:

1. fornecer registros oficiais para screening;
2. disponibilizar aliases e atributos auxiliares para os experimentos de entity resolution;
3. permitir a construção de benchmarks rastreáveis a partir de diferentes representações associadas ao mesmo registro.

O objetivo desta etapa foi transformar o XML oficial em estruturas tabulares validadas e adequadas às análises posteriores, preservando a ligação com o dado de origem.

## 4.2 Dataset e formato selecionado

O arquivo utilizado nesta etapa foi:

SDN_ADVANCED.XML

O formato XML avançado foi selecionado por preservar uma estrutura hierárquica mais rica do que os formatos tabulares simplificados, incluindo informações relacionadas a:

- nomes principais;
- aliases;
- partes componentes dos nomes;
- tipos e subtipos de entidade;
- atributos de identidade;
- documentos e identificadores;
- programas e referências auxiliares.

Arquivos CSV seriam suficientes para diversas aplicações de screening tabular. Entretanto, o XML avançado foi mais adequado aos objetivos deste estudo por permitir investigar a estrutura subjacente dos registros antes de convertê-los em tabelas analíticas.

A escolha não implica superioridade geral do XML, mas adequação ao problema investigado.

## 4.3 Aquisição, preservação e proveniência

O arquivo obtido diretamente da OFAC foi armazenado em:

```text
data/raw/ofac/
```

Essa camada deverá preservar o dado original sem alterações.

Posteriormente, os registros extraídos e normalizados serão gravados em:

data/processed/

O fluxo implementado foi:
```text
OFAC
  ↓
SDN_ADVANCED.XML
  ↓
data/raw/ofac/
  ↓
parser
  ↓
normalização
  ↓
data/processed/
```
Download e transformação permanecem separados, permitindo repetir a aquisição sem executar automaticamente o parser e revisar as transformações sem alterar o arquivo de origem.

A ingestão também utiliza uma estrutura própria de proveniência, com registro temporal em UTC, destinada a preservar a rastreabilidade da **origem dos dados**

### 4.3.1 Proveniência

A origem dos dados foi preservada como parte do processo de ingestão, permitindo distinguir o registro obtido da fonte das transformações realizadas posteriormente.

A implementação registra informações necessárias para rastrear a origem e o momento de obtenção dos dados, incluindo:

- fonte;
- dataset;
- arquivo de origem;
- momento da coleta;
- identificador do registro, quando disponível.

A estrutura de proveniência utiliza timestamps em UTC e permanece separada das transformações analíticas posteriores.

O objetivo é permitir responder questões como:

1. de onde veio determinado registro;
2. quando ele foi obtido;
3. qual arquivo de origem foi utilizado;
4. como o registro de origem se relaciona aos artefatos processados posteriormente.

## 4.4 Inspeção e parsing do XML

Antes da transformação tabular, a estrutura do XML foi inspecionada para identificar os elementos efetivamente utilizados pela OFAC.

Entre os principais componentes observados estão:

```text
DistinctParty
    ↓
Profile
    ↓
Identity
    ↓
Alias / DocumentedName
    ↓
NamePartValue
```
A estrutura também contém Feature, utilizado para representar atributos adicionais de identidade.

A inspeção anterior ao parser evitou impor ao arquivo uma estrutura tabular preconcebida e permitiu definir as tabelas a partir do modelo realmente disponibilizado pela fonte.

O parser foi então desenvolvido para extrair as entidades e suas diferentes representações nominais, mantendo os identificadores necessários para reconstruir sua origem.

## 4.5 Resultados da estruturação

O processamento do `SDN_ADVANCED.XML` resultou em:

| Estrutura | Registros |
|---|---:|
| Entidades OFAC | **19.199** |
| Nomes e aliases | **49.652** |

As entidades foram classificadas em três grupos principais:

| Tipo | Registros |
|---|---:|
| Entity | **9.854** |
| Individual | **7.479** |
| Transport | **1.866** |

A presença de múltiplos nomes por entidade é particularmente importante para o entity resolution, pois permite construir pares positivos utilizando diferentes representações oficialmente associadas ao mesmo registro.

Os arquivos estruturados foram mantidos na camada privada de processamento, evitando a redistribuição desnecessária do dataset derivado completo no repositório público.

## 4.6 Nomes, aliases e complexidade nominal

A análise dos registros mostrou que uma mesma entidade pode possuir múltiplas representações nominais.

Entre os tipos de alias mais frequentes estavam:

- `Name`;
- `A.K.A.` — *also known as*;
- `F.K.A.` — *formerly known as*;
- `N.K.A.` — *now known as*.

Também foram observados diferentes sistemas de escrita, com predominância do alfabeto latino e presença de registros em scripts como cirílico e árabe.

A complexidade nominal variou entre os tipos de entidade. Indivíduos e organizações apresentaram múltiplos nomes e aliases, enquanto transportes tenderam a possuir menor quantidade de representações.

Esse resultado reforça por que uma estratégia exclusivamente baseada em correspondência textual exata é insuficiente para o problema de identidade.

## 4.7 Atributos auxiliares de identidade

Além dos nomes, foram extraídos atributos potencialmente úteis para a desambiguação dos candidatos.

Os principais foram:

- data de nascimento;
- local de nascimento;
- nacionalidade;
- cidadania;
- localização;
- documentos e identificadores.

A disponibilidade desses campos varia conforme o tipo de entidade.

Para os **7.479 registros classificados como `Individual`**, a cobertura observada foi aproximadamente:

| Atributo | Cobertura |
|---|---:|
| Data de nascimento | **98,65%** |
| Nacionalidade | **74,49%** |
| Local de nascimento | **63,62%** |
| Cidadania | **13,97%** |

Essa heterogeneidade é metodologicamente importante: o modelo de matching não pode assumir que todos os candidatos possuem o mesmo conjunto de atributos.

Também é importante distinguir **ausência de informação** de **evidência incompatível**: um atributo não observado não deve ser interpretado automaticamente como divergência entre identidades.

A disponibilidade desigual desses campos motivou posteriormente os testes de robustez com **missingness** e divergências contextuais.

### 4.7.1 Documentos e identificadores

Também foram extraídos documentos associados às entidades.

A cobertura observada foi aproximadamente:

| Tipo | Entidades com documentação |
|---|---:|
| Individual | **56,93%** |
| Entity | **79,73%** |
| Transport | **81,83%** |

Entre os tipos encontrados estavam passaportes, documentos nacionais de identificação, registros fiscais, números empresariais e identificadores específicos de embarcações.

Documentos constituem evidências potencialmente fortes de identidade, mas sua ausência não implica falta de correspondência. Essa distinção também foi testada posteriormente nos experimentos de matching.

## 4.8 Uso da OFAC no benchmark de entity resolution

Os aliases associados oficialmente à mesma entidade foram utilizados na construção dos pares positivos do benchmark.

Conceitualmente:

```text
nome principal
      ↓
alias conhecido
      ↓
mesma entidade OFAC
      ↓
par positivo
```
Os pares positivos são, portanto, derivados de diferentes representações associadas ao **mesmo registro dentro da própria OFAC**.

Essa construção oferece ground truth controlado para o experimento, mas não equivale a uma validação externa com registros independentes de onboarding. Essa limitação é considerada posteriormente na avaliação dos resultados.

## 4.9 Separação entre dados reais e experimentos em grafo

Os registros reais derivados da OFAC são utilizados nas etapas de screening e entity resolution.

A rede pública utilizada posteriormente nos experimentos Neo4j emprega **entidades e referências de risco sintéticas**, evitando apresentar pessoas reais como objetos de uma investigação AML fictícia.

Essa separação preserva a utilidade metodológica da fonte oficial sem misturar registros reais de sanções com cenários transacionais artificiais.

## 4.10 Proveniência, evidência e interpretação

A informação original da OFAC permanece conceitualmente separada dos resultados produzidos pelo pipeline.

Um registro presente na fonte constitui um dado observado. Normalização, matching e scores acrescentam novas camadas analíticas, mas não alteram a natureza ou a proveniência do registro original.

Da mesma forma, um score elevado representa evidência de correspondência de identidade dentro do método utilizado; não constitui, isoladamente, uma decisão de risco ou de compliance.

```text
registro da fonte
      ↓
normalização
      ↓
candidato de matching
      ↓
score / evidências coincidentes
      ↓
priorização
      ↓
revisão humana
```
## 4.11 Síntese da ingestão

A etapa de ingestão estabeleceu o princípio metodológico utilizado no restante do projeto:

> **primeiro compreender e preservar o dado; depois transformá-lo; somente então analisá-lo.**

A estruturação da OFAC produziu uma base com **19.199 entidades e 49.652 nomes e aliases**, enriquecida com atributos de identidade e documentação capazes de alimentar os experimentos posteriores.

O resultado desta etapa pode ser resumido como:

```text
OFAC SDN Advanced
        ↓
inspeção estrutural
        ↓
parser validado
        ↓
entidades + aliases
        ↓
atributos de identidade
        ↓
documentos
        ↓
benchmark de entity resolution
```
