import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

PASTA_DADOS = Path("data/synthetic")

ARQUIVOS_NOS = {
    "Person": ("pessoas.csv", "person_id"),
    "Company": ("empresas.csv", "company_id"),
    "Account": ("contas.csv", "account_id"),
    "Device": ("dispositivos.csv", "device_id"),
    "Address": ("enderecos.csv", "address_id"),
    "RiskEntity": ("entidades_risco.csv", "risk_id"),
}

TIPOS_RELACIONAMENTO = {
    "OWNS",
    "USES_DEVICE",
    "LIVES_AT",
    "REGISTERED_AT",
    "CONTROLS",
    "MATCHED_TO",
}


def carregar_configuracao() -> tuple[str, str, str]:
    """Carrega credenciais locais do Neo4j."""
    load_dotenv()

    uri = os.getenv("NEO4J_URI", "")
    usuario = os.getenv("NEO4J_USERNAME", "")
    senha = os.getenv("NEO4J_PASSWORD", "")

    if not all([uri, usuario, senha]):
        raise ValueError(
            "Credenciais do Neo4j não encontradas no .env."
        )

    return uri, usuario, senha


def preparar_registros(
    arquivo: str,
    coluna_id: str,
) -> list[dict]:
    """Converte um CSV de nós em registros para carga."""
    dados = pd.read_csv(
        PASTA_DADOS / arquivo,
        dtype=str,
    ).fillna("")

    registros = []

    for _, linha in dados.iterrows():
        propriedades = linha.to_dict()

        node_id = str(
            propriedades.pop(coluna_id)
        )

        registros.append(
            {
                "id": node_id,
                "props": {
                    str(chave): str(valor)
                    for chave, valor in propriedades.items()
                },
            }
        )

    return registros


def criar_constraints(
    session,
) -> None:
    """Cria restrições de unicidade para os nós."""
    for label in ARQUIVOS_NOS:
        query = f"""
        CREATE CONSTRAINT {label.lower()}_id_unique
        IF NOT EXISTS
        FOR (n:{label})
        REQUIRE n.id IS UNIQUE
        """

        session.run(query).consume()


def carregar_nos(
    session,
) -> None:
    """Carrega todos os tipos de nós sintéticos."""
    for label, (
        arquivo,
        coluna_id,
    ) in ARQUIVOS_NOS.items():
        registros = preparar_registros(
            arquivo,
            coluna_id,
        )

        query = f"""
        UNWIND $registros AS registro

        MERGE (n:{label} {{
            id: registro.id
        }})

        SET n += registro.props
        """

        session.run(
            query,
            registros=registros,
        ).consume()

        print(
            f"{label:<12} "
            f"{len(registros):>4} nós carregados"
        )


def carregar_relacoes(
    session,
) -> None:
    """Carrega relacionamentos da rede sintética."""
    relacoes = pd.read_csv(
        PASTA_DADOS / "relacoes.csv",
        dtype=str,
    ).fillna("")

    for tipo in sorted(
        relacoes["tipo"].unique()
    ):
        if tipo not in TIPOS_RELACIONAMENTO:
            raise ValueError(
                f"Relacionamento não autorizado: {tipo}"
            )

        grupo = relacoes[
            relacoes["tipo"] == tipo
        ]

        registros = [
            {
                "origem": str(linha["origem"]),
                "destino": str(linha["destino"]),
                "contexto": str(linha["contexto"]),
            }
            for _, linha in grupo.iterrows()
        ]

        query = f"""
        UNWIND $registros AS registro

        MATCH (origem {{
            id: registro.origem
        }})

        MATCH (destino {{
            id: registro.destino
        }})

        MERGE (origem)-[r:{tipo}]->(destino)

        SET r.contexto = registro.contexto
        """

        session.run(
            query,
            registros=registros,
        ).consume()

        print(
            f"{tipo:<15} "
            f"{len(registros):>4} relações carregadas"
        )


def validar_carga(
    session,
) -> None:
    """Confere totais armazenados no Neo4j."""
    resultado_nos = session.run(
        """
        MATCH (n)
        RETURN count(n) AS total
        """
    ).single()

    resultado_relacoes = session.run(
        """
        MATCH ()-[r]->()
        RETURN count(r) AS total
        """
    ).single()

    if (
        resultado_nos is None
        or resultado_relacoes is None
    ):
        raise RuntimeError(
            "Não foi possível validar a carga."
        )

    total_nos = int(
        resultado_nos["total"]
    )

    total_relacoes = int(
        resultado_relacoes["total"]
    )

    print("\nValidação da carga:")
    print(f"Nós no Neo4j:            {total_nos:,}")
    print(
        f"Relacionamentos Neo4j:   "
        f"{total_relacoes:,}"
    )

    if total_nos != 320:
        raise ValueError(
            f"Esperados 320 nós, encontrados {total_nos}."
        )

    if total_relacoes != 366:
        raise ValueError(
            "Esperados 366 relacionamentos, "
            f"encontrados {total_relacoes}."
        )


if __name__ == "__main__":
    neo4j_uri, neo4j_usuario, neo4j_senha = (
        carregar_configuracao()
    )

    with GraphDatabase.driver(
        neo4j_uri,
        auth=(
            neo4j_usuario,
            neo4j_senha,
        ),
    ) as driver:
        driver.verify_connectivity()

        with driver.session(
            database="neo4j"
        ) as session:
            print(
                "\nCriando constraints..."
            )

            criar_constraints(
                session
            )

            print(
                "\nCarregando nós..."
            )

            carregar_nos(
                session
            )

            print(
                "\nCarregando relacionamentos..."
            )

            carregar_relacoes(
                session
            )

            validar_carga(
                session
            )

    print(
        "\nCarga Neo4j concluída com sucesso."
    )
