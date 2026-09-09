import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


def carregar_configuracao() -> tuple[str, str, str]:
    """Carrega as credenciais do Neo4j a partir do arquivo .env."""
    load_dotenv()

    uri = os.getenv("NEO4J_URI", "")
    usuario = os.getenv("NEO4J_USERNAME", "")
    senha = os.getenv("NEO4J_PASSWORD", "")

    if not all([uri, usuario, senha]):
        raise ValueError(
            "Credenciais do Neo4j não encontradas no arquivo .env."
        )

    return uri, usuario, senha


def testar_conexao(
    uri: str,
    usuario: str,
    senha: str,
) -> None:
    """Valida a conexão e executa uma consulta simples."""
    with GraphDatabase.driver(
        uri,
        auth=(usuario, senha),
    ) as driver:
        driver.verify_connectivity()

        registros, _, _ = driver.execute_query(
            """
            RETURN
                'Know Your Networks' AS projeto,
                datetime() AS timestamp
            """,
            database_="neo4j",
        )

        if not registros:
            raise RuntimeError(
                "A conexão foi realizada, mas a consulta não retornou dados."
            )

        registro = registros[0]

        print("\nConexão com Neo4j estabelecida com sucesso.")
        print(f"Projeto: {registro['projeto']}")
        print(f"Timestamp: {registro['timestamp']}")


if __name__ == "__main__":
    neo4j_uri, neo4j_usuario, neo4j_senha = (
        carregar_configuracao()
    )

    testar_conexao(
        neo4j_uri,
        neo4j_usuario,
        neo4j_senha,
    )
