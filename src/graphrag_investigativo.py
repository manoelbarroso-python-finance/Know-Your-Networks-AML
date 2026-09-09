import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.generation.prompts import RagTemplate
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import Text2CypherRetriever

ARQUIVO_SAIDA = Path(
    "data/processed/public/graphrag_person_005.txt"
)

MODELO = "gpt-5.6-luna"

SCHEMA = """
NÓS:

(:Person {
    id: STRING,
    nome: STRING,
    pais: STRING,
    segmento: STRING
})

(:Company {
    id: STRING,
    nome: STRING,
    jurisdicao: STRING
})

(:Account {
    id: STRING,
    tipo: STRING,
    moeda: STRING
})

(:Device {
    id: STRING,
    tipo: STRING
})

(:Address {
    id: STRING,
    descricao: STRING
})

(:RiskEntity {
    id: STRING,
    nome: STRING,
    fonte: STRING,
    categoria: STRING
})

RELACIONAMENTOS:

(:Person)-[:OWNS]->(:Account)
(:Company)-[:OWNS]->(:Account)

(:Person)-[:USES_DEVICE]->(:Device)
(:Person)-[:LIVES_AT]->(:Address)
(:Person)-[:CONTROLS]->(:Company)

(:Company)-[:REGISTERED_AT]->(:Address)

(:Person)-[:MATCHED_TO]->(:RiskEntity)
(:Company)-[:MATCHED_TO]->(:RiskEntity)

(:Account)-[:TRANSFERRED_TO {
    tx_id: STRING,
    valor: FLOAT,
    moeda: STRING,
    timestamp: ZONED_DATETIME
}]->(:Account)
"""

EXEMPLOS = [
    """
Pergunta:
Quais entidades de risco possuem relação direta com PERSON_001?

Cypher:
MATCH
    (p:Person {id: 'PERSON_001'})
    -[:MATCHED_TO]->
    (r:RiskEntity)
RETURN
    p.id AS pessoa,
    r.id AS entidade_risco,
    r.fonte AS fonte,
    r.categoria AS categoria
""",
    """
Pergunta:
Quais dispositivos são utilizados por PERSON_003
e quais outras pessoas utilizam os mesmos dispositivos?

Cypher:
MATCH
    (p:Person {id: 'PERSON_003'})
    -[:USES_DEVICE]->
    (d:Device)
OPTIONAL MATCH
    (outra:Person)
    -[:USES_DEVICE]->
    (d)
WHERE outra <> p
RETURN
    p.id AS pessoa,
    d.id AS dispositivo,
    collect(DISTINCT outra.id) AS outras_pessoas
""",
]

PERGUNTA = """
Analise PERSON_005 como um caso investigativo.

Recupere apenas evidências existentes no grafo que ajudem a
contextualizar o caso, incluindo quando disponíveis:

1. dados básicos da pessoa;
2. entidades RiskEntity diretamente relacionadas;
3. dispositivos utilizados e outras pessoas que compartilham
   esses dispositivos;
4. contas pertencentes à pessoa;
5. transferências recebidas ou enviadas por suas contas em
   20 de julho de 2026, incluindo contraparte, valor e horário.

Não utilize propriedades de ground truth ou pattern_id.
Não faça inferências além dos dados armazenados no grafo.
"""

PROMPT_RELATORIO = RagTemplate(
    system_instructions=(
        "Você atua como analista de apoio a KYC/AML. "
        "Use exclusivamente as evidências recuperadas do Neo4j. "
        "Não trate conexão, centralidade ou comportamento incomum "
        "como prova de atividade ilícita. "
        "Não invente fatos ausentes no contexto. "
        "Diferencie claramente evidência observada de interpretação. "
        "O objetivo é apoiar priorização e revisão humana."
    ),
    template="""
Contexto recuperado do Neo4j:
{context}

Pergunta investigativa:
{query_text}

Produza uma síntese curta em português com esta estrutura:

1. Evidências observadas
2. Contexto relacional
3. Contexto transacional
4. Motivos para revisão
5. Limitações

Não atribua probabilidade de crime, fraude ou lavagem de dinheiro.
Não apresente uma conexão indireta como confirmação de irregularidade.

{examples}
""",
)


@dataclass(frozen=True)
class retriever_result:
    """Representação concreta e segura do resultado do retriever.

    A classe normaliza o objeto retornado pelo GraphRAG e concentra o
    acesso ao Cypher e ao contexto, evitando que o restante do código
    dependa da implementação interna do pacote.
    """

    items: tuple[Any, ...]
    metadata: dict[str, Any]

    @classmethod
    def from_graph_result(cls, resultado: Any) -> "retriever_result":
        """Converte um resultado do GraphRAG em um resultado utilizável."""
        if resultado is None:
            raise RuntimeError("O GraphRAG não retornou contexto.")

        items = tuple(getattr(resultado, "items", ()) or ())
        metadata = dict(getattr(resultado, "metadata", {}) or {})
        return cls(items=items, metadata=metadata)

    def cypher(self) -> str:
        """Retorna o Cypher gerado, quando presente."""
        return str(self.metadata.get("cypher", ""))

    def contexto(self) -> str:
        """Formata os itens recuperados para uso no relatório."""
        return "\n".join(
            str(getattr(item, "content", item))
            for item in self.items
        )


def validar_ambiente() -> tuple[str, str, str]:
    """Valida credenciais necessárias para a prova de conceito."""
    load_dotenv()

    uri = os.getenv("NEO4J_URI", "")
    usuario = os.getenv("NEO4J_USERNAME", "")
    senha = os.getenv("NEO4J_PASSWORD", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if not all(
        [
            uri,
            usuario,
            senha,
        ]
    ):
        raise ValueError(
            "Credenciais do Neo4j não encontradas no .env."
        )

    if not openai_key:
        raise ValueError(
            "OPENAI_API_KEY não encontrada no .env."
        )

    return uri, usuario, senha


def salvar_resultado(
    cypher: str,
    contexto: str,
    resposta: str,
) -> None:
    """Salva evidências da execução para rastreabilidade."""
    ARQUIVO_SAIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conteudo = (
        "GRAPH RAG — PROVA DE CONCEITO\n"
        "================================\n\n"
        f"MODELO\n{MODELO}\n\n"
        f"PERGUNTA\n{PERGUNTA.strip()}\n\n"
        "CYPHER GERADO PELO LLM\n"
        "----------------------\n"
        f"{cypher}\n\n"
        "CONTEXTO RECUPERADO\n"
        "-------------------\n"
        f"{contexto}\n\n"
        "SÍNTESE INVESTIGATIVA\n"
        "---------------------\n"
        f"{resposta}\n"
    )

    ARQUIVO_SAIDA.write_text(
        conteudo,
        encoding="utf-8",
    )


if __name__ == "__main__":
    uri, usuario, senha = validar_ambiente()

    driver = GraphDatabase.driver(
        uri,
        auth=(
            usuario,
            senha,
        ),
    )

    try:
        driver.verify_connectivity()

        llm = OpenAILLM(
            model_name=MODELO,
            model_params={
                "reasoning_effort": "low",
                "max_completion_tokens": 1200,
            },
        )

        retriever = Text2CypherRetriever(
            driver=driver,
            llm=llm,
            neo4j_schema=SCHEMA,
            examples=EXEMPLOS,
            neo4j_database="neo4j",
        )

        rag = GraphRAG(
            retriever=retriever,
            llm=llm,
            prompt_template=PROMPT_RELATORIO,
        )

        print(
            "\nExecutando prova de conceito GraphRAG..."
        )

        resultado = rag.search(
            query_text=PERGUNTA,
            return_context=True,
        )

        resultado_retriever = retriever_result.from_graph_result(
            resultado.retriever_result
        )

        cypher = resultado_retriever.cypher()
        contexto = resultado_retriever.contexto()

        print(
            "\nCypher gerado automaticamente:"
        )
        print(cypher)

        print(
            "\nContexto recuperado do Neo4j:"
        )
        print(contexto)

        print(
            "\nSíntese investigativa:"
        )
        print(resultado.answer)

        salvar_resultado(
            cypher=cypher,
            contexto=contexto,
            resposta=resultado.answer,
        )

        print(
            "\nResultado salvo em: "
            "data/processed/public/"
            "graphrag_person_005.txt"
        )

    finally:
        driver.close()
