from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

from src.conexao_neo4j import carregar_configuracao

ARQUIVO_TRANSACOES = Path(
    "data/synthetic/transacoes.csv"
)


def carregar_transacoes() -> list[dict]:
    """Carrega e prepara as transações sintéticas."""
    dados = pd.read_csv(
        ARQUIVO_TRANSACOES,
        dtype={
            "tx_id": str,
            "origem": str,
            "destino": str,
            "moeda": str,
            "pattern_id": str,
        },
    ).fillna("")

    dados["valor"] = pd.to_numeric(
        dados["valor"],
        errors="raise",
    )

    dados["timestamp"] = pd.to_datetime(
        dados["timestamp"],
        errors="raise",
    )

    dados["ground_truth"] = (
        dados["ground_truth"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    registros = []

    for _, linha in dados.iterrows():
        timestamp = linha["timestamp"]

        registros.append(
            {
                "tx_id": str(
                    linha["tx_id"]
                ),
                "origem": str(
                    linha["origem"]
                ),
                "destino": str(
                    linha["destino"]
                ),
                "valor": float(
                    linha["valor"]
                ),
                "moeda": str(
                    linha["moeda"]
                ),
                "timestamp": (
                    timestamp.isoformat()
                ),
                "ground_truth": bool(
                    linha["ground_truth"]
                ),
                "pattern_id": str(
                    linha["pattern_id"]
                ),
            }
        )

    return registros


def carregar_no_neo4j(
    driver,
    transacoes: list[dict],
) -> None:
    """Cria os relacionamentos transacionais."""
    query = """
    UNWIND $transacoes AS tx

    MATCH (origem:Account {
        id: tx.origem
    })

    MATCH (destino:Account {
        id: tx.destino
    })

    MERGE (origem)-[
        r:TRANSFERRED_TO {
            tx_id: tx.tx_id
        }
    ]->(destino)

    SET
        r.valor = tx.valor,
        r.moeda = tx.moeda,
        r.timestamp = datetime(tx.timestamp),
        r.ground_truth = tx.ground_truth,
        r.pattern_id = tx.pattern_id
    """

    driver.execute_query(
        query,
        transacoes=transacoes,
        database_="neo4j",
    )


def validar_carga(driver) -> None:
    """Confere a quantidade de transações no grafo."""
    registros, _, _ = driver.execute_query(
        """
        MATCH ()-[r:TRANSFERRED_TO]->()

        RETURN
            count(r) AS total,
            sum(
                CASE
                    WHEN r.ground_truth = true
                    THEN 1
                    ELSE 0
                END
            ) AS ground_truth
        """,
        database_="neo4j",
    )

    if not registros:
        raise RuntimeError(
            "A validação da carga não retornou dados."
        )

    resultado = registros[0]

    total = int(
        resultado["total"]
    )

    ground_truth = int(
        resultado["ground_truth"] or 0
    )

    print(
        "\nValidação da carga transacional:"
    )

    print(
        f"Transações Neo4j:          "
        f"{total:,}"
    )

    print(
        f"Transações ground truth:   "
        f"{ground_truth:,}"
    )

    if total != 458:
        raise ValueError(
            "Esperadas 458 transações; "
            f"encontradas {total}."
        )

    if ground_truth != 8:
        raise ValueError(
            "Esperadas 8 transações de ground truth; "
            f"encontradas {ground_truth}."
        )


if __name__ == "__main__":
    uri, usuario, senha = (
        carregar_configuracao()
    )

    transacoes = carregar_transacoes()

    print(
        f"\nTransações preparadas para carga: "
        f"{len(transacoes):,}"
    )

    with GraphDatabase.driver(
        uri,
        auth=(
            usuario,
            senha,
        ),
    ) as driver:
        driver.verify_connectivity()

        carregar_no_neo4j(
            driver,
            transacoes,
        )

        validar_carga(
            driver
        )

    print(
        "\nCarga transacional concluída "
        "com sucesso."
    )
