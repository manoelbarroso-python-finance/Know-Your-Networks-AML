import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

ARQUIVO_EXPOSICOES = Path(
    "data/processed/public/neo4j_exposicoes_detectadas.csv"
)

ARQUIVO_METRICAS = Path(
    "data/processed/public/neo4j_metricas_exposicao.csv"
)

TIPOS_PERMITIDOS = [
    "MATCHED_TO",
    "CONTROLS",
    "USES_DEVICE",
    "LIVES_AT",
    "REGISTERED_AT",
]

GROUND_TRUTH = {
    ("PERSON_001", "RISK_001"),
    ("PERSON_002", "RISK_002"),
    ("PERSON_003", "RISK_003"),
    ("PERSON_004", "RISK_003"),
    ("PERSON_005", "RISK_003"),
    ("PERSON_006", "RISK_004"),
}


def carregar_configuracao() -> tuple[str, str, str]:
    """Carrega as credenciais locais do Neo4j."""
    load_dotenv()

    uri = os.getenv("NEO4J_URI", "")
    usuario = os.getenv("NEO4J_USERNAME", "")
    senha = os.getenv("NEO4J_PASSWORD", "")

    if not all([uri, usuario, senha]):
        raise ValueError(
            "Credenciais do Neo4j não encontradas no .env."
        )

    return uri, usuario, senha


def buscar_exposicoes(driver) -> pd.DataFrame:
    """Busca caminhos de até três saltos até entidades de risco."""
    query = """
    MATCH path =
        (p:Person)-[*1..3]-(r:RiskEntity)

    WHERE all(
        rel IN relationships(path)
        WHERE type(rel) IN $tipos
    )

    RETURN
        p.id AS pessoa,
        r.id AS entidade_risco,
        length(path) AS saltos,
        [rel IN relationships(path) | type(rel)]
            AS tipos_relacao,
        [n IN nodes(path) | n.id]
            AS caminho
    """

    registros, _, _ = driver.execute_query(
        query,
        tipos=TIPOS_PERMITIDOS,
        database_="neo4j",
    )

    dados = pd.DataFrame(
        [
            {
                "pessoa": registro["pessoa"],
                "entidade_risco": registro["entidade_risco"],
                "saltos": int(registro["saltos"]),
                "tipos_relacao": " > ".join(
                    registro["tipos_relacao"]
                ),
                "caminho": " > ".join(
                    registro["caminho"]
                ),
            }
            for registro in registros
        ]
    )

    if dados.empty:
        raise RuntimeError(
            "Nenhuma exposição foi encontrada no Neo4j."
        )

    # Um mesmo par pode possuir mais de um caminho.
    # Mantemos o caminho mais curto.
    dados = (
        dados.sort_values("saltos")
        .drop_duplicates(
            subset=[
                "pessoa",
                "entidade_risco",
            ],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return dados


def calcular_metricas(
    metodo: str,
    candidatos: set[tuple[str, str]],
) -> dict:
    """Compara candidatos detectados ao ground truth."""
    verdadeiros_positivos = (
        candidatos & GROUND_TRUTH
    )

    falsos_positivos = (
        candidatos - GROUND_TRUTH
    )

    falsos_negativos = (
        GROUND_TRUTH - candidatos
    )

    tp = len(verdadeiros_positivos)
    fp = len(falsos_positivos)
    fn = len(falsos_negativos)

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "metodo": metodo,
        "candidatos": len(candidatos),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def marcar_ground_truth(
    exposicoes: pd.DataFrame,
) -> pd.DataFrame:
    """Identifica quais exposições pertencem ao ground truth."""
    resultado = exposicoes.copy()

    resultado["ground_truth"] = [
        (
            pessoa,
            risco,
        )
        in GROUND_TRUTH
        for pessoa, risco in zip(
            resultado["pessoa"],
            resultado["entidade_risco"],
            strict=True,
        )
    ]

    resultado["tipo_exposicao"] = (
        resultado["saltos"]
        .eq(1)
        .map(
            {
                True: "Direta",
                False: "Indireta",
            }
        )
    )

    return resultado


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

        exposicoes = buscar_exposicoes(
            driver
        )

    exposicoes = marcar_ground_truth(
        exposicoes
    )

    candidatos_diretos = set(
        exposicoes.loc[
            exposicoes["saltos"] == 1,
            [
                "pessoa",
                "entidade_risco",
            ],
        ].itertuples(
            index=False,
            name=None,
        )
    )

    candidatos_rede = set(
        exposicoes[
            [
                "pessoa",
                "entidade_risco",
            ]
        ].itertuples(
            index=False,
            name=None,
        )
    )

    metricas = pd.DataFrame(
        [
            calcular_metricas(
                "Screening direto",
                candidatos_diretos,
            ),
            calcular_metricas(
                "Rede até 3 saltos",
                candidatos_rede,
            ),
        ]
    )

    ARQUIVO_EXPOSICOES.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    exposicoes.to_csv(
        ARQUIVO_EXPOSICOES,
        index=False,
        encoding="utf-8",
    )

    metricas.to_csv(
        ARQUIVO_METRICAS,
        index=False,
        encoding="utf-8",
    )

    print("\nExposições únicas encontradas:")
    print(len(exposicoes))

    print("\nGround truth esperado:")
    print(len(GROUND_TRUTH))

    print("\nComparação dos métodos:")
    print(
        metricas.to_string(
            index=False
        )
    )

    print("\nExposições relevantes recuperadas:")

    print(
        exposicoes[
            exposicoes["ground_truth"]
        ][
            [
                "pessoa",
                "entidade_risco",
                "saltos",
                "tipo_exposicao",
                "caminho",
            ]
        ].to_string(
            index=False
        )
    )

    print("\nCandidatos adicionais da rede:")

    print(
        exposicoes[
            ~exposicoes["ground_truth"]
        ][
            [
                "pessoa",
                "entidade_risco",
                "saltos",
                "tipos_relacao",
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )
