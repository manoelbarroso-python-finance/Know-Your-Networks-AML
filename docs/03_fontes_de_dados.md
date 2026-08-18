# Fontes de dados e inteligência externa

1. Objetivo

A qualidade de um processo de KYC, screening ou investigação financeira depende não apenas dos métodos analíticos utilizados, mas também da qualidade, cobertura, atualidade e rastreabilidade das informações consultadas.

Este projeto utilizará uma combinação de:

- fontes oficiais;
- bases públicas;
- APIs especializadas;
- dados corporativos;
- dados sintéticos e semissintéticos;
- fontes complementares de inteligência externa.

A intenção não é maximizar o número de bases consultadas.

Cada fonte deverá responder a uma necessidade concreta dentro da investigação.

2. Princípios para seleção das fontes

Uma fonte será incorporada quando apresentar valor em pelo menos uma das seguintes dimensões:

2.1 autoridade da informação;
2.2 cobertura;
2.3 qualidade dos identificadores;
2.4 capacidade de integração por API ou arquivo estruturado;
2.5 utilidade para entity resolution;
2.6 capacidade de revelar relacionamentos;
2.7 reprodutibilidade;
2.8 custo compatível com a proposta experimental.

Fontes pagas não serão automaticamente excluídas.

Um custo reduzido poderá ser aceito quando houver ganho mensurável de cobertura, qualidade ou capacidade investigativa.

O objetivo será sempre justificar:

**o que essa fonte acrescentou que não estava disponível anteriormente?**

3. Fontes inicialmente selecionadas:

**Fonte**  **função principal**  **forma de acesso**  **custo**   **papel inicial**

Open       Screening e                API           Pay-as-      Principal benchmark
Santions   entity matching                          you-go       externo

OFAC        Sanções oficiais       Arquivos        Gratuito      Ground truth oficial
            dos EUA              Estruturados

ONU           Sanções         XML/Dados oficiais   Gratuito      Validação internacional
            Multilaterais

Portal da     Pessoas expostas    Dados abertos    Gratuito      Contexto Brasileiro
Transparência  Politicamente
PEP

Portal da     Sanções ADM       API/Dados abertos  Gratuito      integridade e riscos
Transparência                                                        de terceiros
CEIS/CNEP

GLEIF        Identificação e         API           Gratuito      Enriquecimento empresarial
          relações corporativas

GDELT       Midia e contexto   API/Dados abertos   Gratuito      Camada experimental posterior
               Externos

A utilização de todas essas fontes em uma mesma análise não será obrigatória.

O pipeline será desenvolvido por etapas.

4. OpenSanctions
4.1 Papel no projeto

O OpenSanctions será utilizado como uma das principais referências externas para:

-pessoas sancionadas;
-empresas sancionadas;
-Pessoas Expostas Politicamente;
-aliases;
-identificadores;
-entidades relacionadas;
-outras categorias de interesse para compliance.

O principal objetivo não será apenas consultar registros.

O OpenSanctions será utilizado como benchmark de entity resolution e screening.

4.2 Endpoint de matching

Para screening, será utilizado prioritariamente o endpoint:

/match

em vez de uma busca textual simples.

A diferença metodológica é importante.

Uma pesquisa baseada apenas no nome pode produzir muitos candidatos semelhantes.

O matching poderá considerar simultaneamente atributos como:

-nome
-data de nascimento
-nacionalidade
-identificador fiscal
-endereço
-tipo de entidade

Isso permitirá comparar:

Exact Match
    ↓
Nome normalizado
    ↓
Fuzzy matching
    ↓
Matching multivariado próprio
    ↓
OpenSanctions /match

4.3 Reprodutibilidade do algoritmo

Para experimentos comparativos, o projeto buscará utilizar uma versão identificável do algoritmo de matching.

Quando disponível, será preferível fixar uma implementação recomendada e estável em vez de utilizar automaticamente uma configuração que possa mudar ao longo do tempo.

A versão ou configuração utilizada deverá ser registrada juntamente com a data do experimento.

Isso evita que alterações futuras no serviço modifiquem silenciosamente os resultados históricos do benchmark.

4.4 Controle de custo

O OpenSanctions será utilizado de maneira seletiva.

Em vez de enviar indiscriminadamente toda a base para uma API paga, o pipeline poderá executar:

normalização local
        ↓
filtros iniciais
        ↓
matching local
        ↓
candidatos relevantes
        ↓
OpenSanctions API

Essa arquitetura permite utilizar uma API especializada apenas onde ela realmente agrega informação.

Também cria um experimento adicional:

**Quanto o serviço especializado melhora o resultado em relação ao nosso pipeline local?**

5. OFAC
5.1 Papel no projeto

A Office of Foreign Assets Control (OFAC) será utilizada como uma fonte oficial de sanções.

Serão consideradas principalmente:

Specially Designated Nationals and Blocked Persons List — SDN;
Consolidated Non-SDN List.

Os dados estruturados permitem construir uma base de referência diretamente a partir da autoridade responsável pela publicação.

5.2 Por que manter OFAC e OpenSanctions

As duas fontes não serão tratadas como redundantes.

A OFAC representa:

fonte oficial

enquanto o OpenSanctions representa:

camada agregada + normalização + matching

Essa diferença permitirá testar uma pergunta importante:

Qual é o valor acrescentado por uma camada especializada de agregação e entity matching em relação ao consumo direto da lista oficial?

5.3 Utilização em entity resolution

Registros oficiais contendo aliases ou diferentes formas de identificação poderão contribuir para a construção de pares positivos.

Exemplo conceitual:

Registro oficial:
ENTITY_001

Alias A
Alias B
Alias C

Como os aliases pertencem ao mesmo registro oficial, eles poderão servir como exemplos controlados de diferentes representações da mesma entidade.

Também poderão ser criadas perturbações sintéticas adicionais:

remoção de hífen
remoção de acento
abreviação
alteração de ordem
erro tipográfico
transliteração

Isso permitirá medir objetivamente a robustez do matching.

6. Lista Consolidada das Nações Unidas

A lista consolidada do Conselho de Segurança das Nações Unidas será considerada como uma segunda referência oficial internacional.

Seu papel será principalmente:

-ampliar a diversidade jurisdicional;
-testar diferentes formatos de nomes e aliases;
-validar o comportamento do pipeline fora de uma única fonte nacional;
-fornecer casos adicionais para entity resolution.

A ONU será tratada como fonte oficial independente e não apenas como informação herdada de um agregador.

7. Pessoas Expostas Politicamente — Brasil
7.1 Fonte

O Portal da Transparência disponibiliza dados abertos relacionados a Pessoas Expostas Politicamente.

Essa fonte permitirá introduzir uma dimensão brasileira ao projeto.

7.2 Interpretação

A presença de uma pessoa em um cadastro de PEP não representa evidência de irregularidade.

No modelo investigativo:

PEP ≠ irregularidade

A condição será representada como um atributo relevante para diligência e contexto.

Exemplo:

(:Pessoa)-[:POSSUI_CLASSIFICACAO]->(:PEP)

e não:

(:Pessoa)-[:COMETEU]->(:Irregularidade)

7.3 Proteção dos identificadores

A base pública pode conter identificadores pessoais.

O projeto não publicará esses identificadores quando não forem indispensáveis para compreender o experimento.

A camada pública do repositório deverá utilizar:

PERSON_0001
PERSON_0002
PERSON_0003

ou outro processo de pseudonimização definido posteriormente.

A identidade real não será necessária para demonstrar o funcionamento da análise.

8. CEIS e CNEP
8.1 CEIS

O Cadastro Nacional de Empresas Inidôneas e Suspensas reúne registros de pessoas físicas ou jurídicas sujeitas a determinadas sanções administrativas.

8.2 CNEP

O Cadastro Nacional de Empresas Punidas reúne registros relacionados a sanções aplicadas a pessoas jurídicas.

8.3 Papel no projeto

Essas fontes não serão tratadas automaticamente como listas AML.

Elas servirão como exemplos de:

-risco de integridade;
-sanções administrativas;
-risco de terceiros;
-relacionamentos empresariais potencialmente relevantes.

No grafo, poderão gerar estruturas como:

(:Empresa)-[:RECEBEU_SANCAO]->(:SancaoAdministrativa)

ou:

(:Pessoa)-[:ASSOCIADA_A]->(:RegistroAdministrativo)

8.4 API versus download

O projeto poderá demonstrar as duas estratégias.

Consulta por API

Adequada para:

-consultas pontuais;
-integração programática;
-demonstração do pipeline.
-Dataset completo

Adequado para:

-grandes volumes;
-análises locais;
-reprodutibilidade;
-redução do número de chamadas.

A escolha será feita de acordo com o experimento.

9. GLEIF
9.1 Identificação de entidades jurídicas

A Global Legal Entity Identifier Foundation será utilizada para enriquecer empresas que possuam Legal Entity Identifier — LEI.

A informação poderá incluir:

LEI;
nome legal;
jurisdição;
endereço;
situação do registro;
identificadores relacionados.

9.2 Relações corporativas

Um dos principais interesses será a camada de relacionamentos corporativos.

Exemplo:

Empresa A
   │
   ├── controladora direta → Empresa B
   │
   └── controladora final → Empresa C

Isso poderá ser convertido diretamente em relações do Neo4j:

(:Empresa)-[:CONTROLADA_DIRETAMENTE_POR]->(:Empresa)

(:Empresa)-[:CONTROLADA_EM_ULTIMA_INSTANCIA_POR]->(:Empresa)

Essa camada será particularmente relevante para a ideia de Know Your Networks.

9.3 Limitação

Nem toda empresa possui LEI.

Portanto, ausência de registro na GLEIF não deverá ser interpretada como ausência ou inexistência da empresa.

GLEIF será uma fonte de enriquecimento, não um cadastro corporativo universal.

10. Mídia adversa — camada experimental

Mídia adversa apresenta um desafio diferente das listas estruturadas.

Uma notícia pode representar:

mera menção;
alegação;
investigação;
denúncia formal;
decisão administrativa;
condenação;
absolvição;
arquivamento.

Portanto:

notícia encontrada ≠ fato comprovado

10.1 GDELT

O GDELT poderá ser avaliado como fonte gratuita para descoberta inicial de notícias e contexto.

Seu valor potencial está na capacidade de pesquisar grande volume de cobertura jornalística internacional.

Entretanto, os resultados apresentam riscos importantes:

homônimos;
duplicações;
diferentes níveis de qualidade editorial;
associação incorreta entre pessoa e matéria;
ausência de contexto jurídico;
eventos antigos ou desatualizados.

Por isso, essa camada não será utilizada inicialmente como ground truth.

10.2 Estratégia investigativa

Uma arquitetura possível será:

entidade
   ↓
screening estruturado
   ↓
sinal relevante
   ↓
pesquisa de mídia
   ↓
artigos candidatos
   ↓
entity resolution
   ↓
contexto
   ↓
revisão

Dessa forma, mídia adversa funcionará como enriquecimento investigativo, não como mecanismo automático de classificação.

11. APIs pagas de baixo custo

O projeto manterá aberta a possibilidade de incorporar uma API paga quando houver ganho concreto.

O orçamento experimental será deliberadamente limitado.

Uma nova API somente será adicionada quando pudermos formular uma hipótese do tipo:

A utilização desta fonte deve aumentar a cobertura ou reduzir determinada falha observada.

Depois será possível testar se isso realmente ocorreu.

Uma ferramenta paga que não melhorar o resultado será documentada como tal.

Isso também faz parte da avaliação do stack.

12. Hierarquia das fontes

Nem todas as fontes terão o mesmo peso.

Uma hierarquia conceitual será utilizada:

FONTE OFICIAL
     │
     ▼
BASE ESPECIALIZADA / AGREGADOR
     │
     ▼
REGISTRO CORPORATIVO
     │
     ▼
MÍDIA / CONTEXTO ABERTO
     │
     ▼
INFERÊNCIA ANALÍTICA

Quando duas fontes divergirem, o projeto deverá preservar a divergência em vez de simplesmente escolher silenciosamente uma delas.

13. Proveniência dos dados

Todo registro externo relevante deverá preservar informações sobre sua origem.

Campos conceituais:

source_name
source_dataset
source_record_id
source_type
retrieved_at
source_last_updated
source_version

Quando necessário, também poderão ser armazenados:

request_parameters
matching_algorithm
matching_threshold
raw_record_hash

O objetivo será permitir responder:

De onde veio esta informação?

Quando ela foi coletada?

Qual registro original a originou?

Qual transformação foi aplicada?

14. Preservação do dado original

Sempre que possível, haverá separação entre:

RAW
↓
PROCESSADO
↓
ANALÍTICO
data/raw/

Contém o dado original obtido da fonte.

Não será versionado publicamente quando houver risco de exposição ou volume desnecessário.

data/processed/

Contém dados já:

limpos;
normalizados;
selecionados;
pseudonimizados quando necessário.

Somente arquivos adequados à publicação poderão entrar no repositório.

data/synthetic/

Contém entidades e transações artificiais criadas especificamente para os experimentos.

Essa camada poderá ser integralmente reproduzível.

15. Separação entre fonte e classificação

Uma propriedade fundamental será evitar transformar a origem do registro em julgamento.

Por exemplo:

source = "PEP"

não implica:

risk = "alto"

Da mesma forma:

source = "mídia"

não implica:

evidence = "confirmed"

O pipeline deverá preservar separadamente:

fonte
categoria
match
confiança
contexto
evidência
decisão

16. Primeira fase operacional

Para controlar o escopo, a primeira implementação utilizará um conjunto reduzido de fontes.

Núcleo inicial
OFAC
OpenSanctions
Portal da Transparência
GLEIF

Essas quatro camadas já permitem testar:

ingestão de arquivos;
consumo de APIs;
normalização;
entity resolution;
screening;
sanções;
PEP;
integridade;
estruturas corporativas;
relações no Neo4j.
Expansão posterior

Depois que o núcleo estiver validado, poderão ser incorporados:

ONU
mídia adversa
outras fontes corporativas
APIs adicionais
GraphRAG

Isso evita adicionar complexidade antes de validar o pipeline principal.

17. Perguntas que as fontes deverão responder

Ao final, será possível avaliar:

Cobertura

Quantas entidades relevantes cada fonte consegue recuperar?

Qualidade de matching

Quais fontes fornecem atributos suficientes para reduzir falsos positivos?

Complementaridade

Uma fonte encontra registros que outra não encontra?

Estrutura relacional

Quais bases acrescentam relacionamentos úteis ao grafo?

Custo-benefício

Uma API paga produz ganho mensurável em relação às alternativas gratuitas?

Proveniência

É possível rastrear cada resultado até sua origem?

18. Limitações

Nenhuma dessas fontes será tratada como completa.

Entre as limitações esperadas estão:

diferenças de cobertura geográfica;
diferentes frequências de atualização;
registros incompletos;
aliases ausentes;
inconsistências entre jurisdições;
empresas sem LEI;
dificuldade de entity resolution;
falsos positivos;
mídia descontextualizada.

O objetivo não será ocultar essas limitações.

Elas farão parte dos resultados do projeto.

19. Critério para inclusão de novas fontes

Antes de incluir uma nova API ou dataset, serão respondidas quatro perguntas:

Qual problema ela resolve?
Qual informação nova ela fornece?
Como seu benefício será medido?
O custo e a complexidade são proporcionais ao ganho?

Se essas perguntas não tiverem uma resposta clara, a fonte não será adicionada.

20. Resultado esperado desta camada

Ao final da etapa de inteligência externa, o projeto deverá possuir registros padronizados capazes de alimentar as etapas seguintes:

fontes externas
        ↓
dados normalizados
        ↓
entity resolution
        ↓
screening
        ↓
entidades e relações
        ↓
Neo4j

A qualidade dessa camada será fundamental para todas as análises posteriores.

Um grafo sofisticado construído sobre identidades incorretamente resolvidas apenas produziria uma representação sofisticada de relações erradas.

Por isso, qualidade da fonte, proveniência e entity resolution serão tratados como componentes centrais do projeto, e não apenas como preparação de dados.
