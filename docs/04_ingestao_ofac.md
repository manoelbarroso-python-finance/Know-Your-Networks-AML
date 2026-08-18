# Ingestão da OFAC — baseline oficial de sanções

## 1. Objetivo

A primeira ingestão de dados reais do projeto utilizará a lista de **Specially Designated Nationals and Blocked Persons (SDN)**, publicada pela **Office of Foreign Assets Control (OFAC)**.

A escolha da OFAC como primeira fonte tem um propósito metodológico.

Antes de utilizar agregadores, mecanismos externos de matching ou bases enriquecidas, o projeto estabelecerá um **baseline construído diretamente a partir de uma fonte oficial**.

Isso permitirá posteriormente comparar:

```text
Fonte oficial
     ↓
normalização própria
     ↓
matching próprio
     ↓
agregadores e APIs especializadas

2. Dataset selecionado

Será utilizado inicialmente o arquivo:

SDN_ADVANCED.XML

O formato avançado foi escolhido porque mantém os dados essenciais da SDN List e disponibiliza uma estrutura mais rica de metadados.

Isso é especialmente relevante para um projeto que pretende explorar:

-aliases;
-diferentes representações de nomes;
-identificadores;
-atributos associados a entidades;
-relações entre registros;
-screening;
-entity resolution.

O uso do XML também preserva uma estrutura hierárquica que poderá ser explorada antes da transformação para formatos tabulares ou para o Neo4j.

3. Por que não começar pelo CSV

A OFAC também disponibiliza arquivos CSV e outros formatos mais simples.

Esses formatos são adequados para diversos tipos de integração e seriam suficientes para uma análise puramente tabular.

Entretanto, este projeto pretende avaliar não apenas os registros principais, mas também atributos e relacionamentos associados a cada entidade.

Por isso, o XML avançado será utilizado como primeira fonte.

Isso não significa que o CSV seja inferior para todas as aplicações.

A decisão reflete apenas os objetivos específicos deste projeto.

4. Separação entre dado bruto e dado processado

O arquivo obtido diretamente da OFAC será armazenado em:

data/raw/ofac/

Essa camada deverá preservar o dado original sem alterações.

Posteriormente, os registros extraídos e normalizados serão gravados em:

data/processed/

O fluxo será:

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

O dado bruto não deverá ser modificado pelo processo de transformação.

Caso uma nova versão seja obtida, sua coleta deverá ser rastreável.

5. Proveniência

A ingestão deverá registrar informações suficientes para identificar a origem do dado.

Entre elas:

fonte;
dataset;
momento da coleta;
arquivo original;
identificador do registro.

Posteriormente poderão ser adicionados:

hash do arquivo;
data de publicação;
versão do schema.

Isso permitirá responder perguntas como:

De onde veio este registro?

Quando ele foi coletado?

Qual versão do dataset foi utilizada?

Dois experimentos utilizaram exatamente o mesmo snapshot?

6. Integridade do arquivo

Uma etapa posterior poderá calcular um hash criptográfico SHA-256 do arquivo bruto.

Conceitualmente:

SDN_ADVANCED.XML
        ↓
      SHA-256
        ↓
hash do snapshot utilizado

O objetivo não será criptografar o dataset.

O hash funcionará como uma impressão digital do arquivo, permitindo identificar precisamente o snapshot utilizado em determinado experimento.

Essa informação será especialmente útil para:

reprodutibilidade;
auditoria;
comparação entre versões;
documentação dos experimentos.

7. Primeira etapa de ingestão

A ingestão será dividida deliberadamente em duas fases.

7.1 Fase 1 — download

Responsabilidades:

acessar a fonte oficial;
verificar a resposta HTTP;
salvar o arquivo bruto;
registrar data e hora da coleta;
preservar o conteúdo recebido.

Nenhum parsing será realizado nesta fase.

7.2 Fase 2 — interpretação

Somente depois de confirmar que o arquivo foi obtido corretamente será iniciada a análise da estrutura XML.

Essa separação evita misturar:

aquisição

com:

transformação

e torna o pipeline mais fácil de testar, compreender e auditar.

8. Princípio de preservação

O arquivo original será tratado como evidência daquilo que foi efetivamente disponibilizado pela fonte no momento da coleta.

Transformações como:

-normalização de nomes;
-extração de aliases;
-conversão de datas;
-classificação de atributos;
-construção de tabelas;
-preparação de entidades para o grafo;

ocorrerão apenas em etapas posteriores.

Assim, sempre será possível retornar ao dado original caso seja necessário revisar uma transformação.

Esse princípio estabelece três camadas distintas:

RAW
 ↓
PROCESSADO
 ↓
ANALÍTICO

Cada camada terá uma função específica e não deverá modificar retroativamente a camada anterior.

9. Relação futura com o Neo4j

A ingestão da OFAC deverá produzir posteriormente entidades que possam ser representadas aproximadamente como:

(:EntidadeOFAC)
      │
      ├── POSSUI_ALIAS
      │
      ├── POSSUI_ENDERECO
      │
      ├── POSSUI_IDENTIFICADOR
      │
      └── ASSOCIADA_A_PROGRAMA

Essa representação ainda não será criada nesta etapa.

Primeiro será necessário compreender e validar a estrutura dos registros de origem.

A modelagem no Neo4j será definida a partir das relações efetivamente observadas nos dados e não apenas de uma estrutura previamente imaginada.

10. Relação futura com entity resolution

A OFAC também fornecerá parte do ground truth utilizado posteriormente para avaliar os métodos de matching.

A estrutura poderá permitir construir casos como:

nome principal
      ↓
alias conhecido
      ↓
mesma entidade oficial

Como diferentes nomes estão associados oficialmente ao mesmo registro, eles poderão funcionar como exemplos positivos para testes de entity resolution.

Esses pares poderão ser utilizados posteriormente para comparar:

-exact matching;
-nome normalizado;
-fuzzy matching;
-matching multivariado;
-OpenSanctions.

Além dos aliases existentes, poderão ser introduzidas perturbações sintéticas controladas, como:

-remoção de acentos;
-alteração de ordem;
-retirada de hífens;
-abreviações;
-pequenas alterações tipográficas;
-transliterações.

Dessa maneira, será possível medir objetivamente a robustez dos diferentes métodos.

11. Relação com a proveniência do projeto

Os objetos e registros produzidos a partir da OFAC deverão manter uma ligação explícita com a fonte original.

Conceitualmente:

registro OFAC
      ↓
proveniência
      ↓
normalização
      ↓
matching
      ↓
entidade no grafo
      ↓
resultado investigativo

Essa cadeia será importante posteriormente quando o projeto incorporar:

-Neo4j;
-Graph Analytics;
-GraphRAG;
-geração assistida por LLM.

O objetivo será permitir que uma conclusão ou afirmação investigativa possa ser rastreada até a informação que lhe deu origem.

12. Separação entre dado e interpretação

A presença de uma entidade em uma lista oficial será tratada como uma característica proveniente da fonte, e não como uma inferência criada pelo projeto.

Da mesma forma, uma correspondência potencial encontrada pelo pipeline será mantida separada da informação original.

Por exemplo:

registro_original = OFAC

não é a mesma coisa que:

match_confirmado = True

O pipeline deverá distinguir:

-registro original;
-candidato encontrado;
-score de matching;
-atributos coincidentes;
-atributos divergentes;
-interpretação;
-revisão humana.

Essa separação será fundamental para reduzir a confusão entre fonte, evidência e decisão.

13. Critério de sucesso desta etapa

A primeira ingestão será considerada bem-sucedida quando:

o arquivo oficial puder ser obtido de forma reproduzível;
o arquivo bruto for salvo sem transformação;
a origem e o momento da coleta forem registrados;
o pipeline conseguir detectar erros HTTP;
nenhuma informação do arquivo for silenciosamente alterada durante o download;
o snapshot utilizado puder ser posteriormente identificado;
a etapa de download puder ser executada independentemente do parser.

Somente depois dessas validações o XML será interpretado.

14. Perguntas que esta etapa deverá responder

Antes de avançar para o parsing, será necessário responder:

Aquisição

O arquivo oficial pode ser obtido de forma automatizada e reproduzível?

Integridade

É possível verificar se o arquivo utilizado em dois experimentos é exatamente o mesmo?

Proveniência

Conseguimos registrar claramente quando, onde e como o dado foi obtido?

Separação de responsabilidades

Download e transformação estão suficientemente separados para permitir auditoria independente?

Reprodutibilidade

Outra pessoa poderia repetir a coleta e compreender qual snapshot foi utilizado?

15. Próxima etapa

Após a validação do download, o projeto analisará a estrutura interna do XML para identificar:

registros principais;
nomes;
aliases;
tipos de entidade;
identificadores;
endereços;
programas de sanções;
datas;
jurisdições;
demais atributos úteis.

Somente depois dessa inspeção será definida a estrutura tabular utilizada nas análises seguintes.

O fluxo esperado será:

DOWNLOAD
   ↓
SNAPSHOT BRUTO
   ↓
VALIDAÇÃO
   ↓
INSPEÇÃO DO XML
   ↓
PARSER
   ↓
NORMALIZAÇÃO
   ↓
ENTITY RESOLUTION

Essa decisão evita impor ao dataset uma estrutura preconcebida antes de compreender o modelo fornecido pela fonte.

16. Princípio metodológico

Esta primeira ingestão estabelece um princípio que será repetido ao longo do projeto:

primeiro compreender e preservar o dado; depois transformá-lo; somente então analisá-lo.

Esse princípio será aplicado posteriormente às demais fontes externas e às relações carregadas no Neo4j.

A sofisticação das etapas posteriores — incluindo graph analytics e GraphRAG — dependerá diretamente da qualidade, rastreabilidade e consistência das informações produzidas nesta camada inicial.
