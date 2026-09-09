import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

ARQUIVO_SAIDA = Path(
    "data/processed/public/neo4j_analise_caminhos.csv"
)

ARQUIVO_RESUMO = Path(
    "data/processed/public/neo4j_resumo_tipos_caminho.csv"
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
    """Carrega as credenciais do Neo4j."""
    load_dotenv()

    uri = os.getenv("NEO4J_URI", "")
    usuario = os.getenv("NEO4J_USERNAME", "")
    senha = os.getenv("NEO4J_PASSWORD", "")

    if not all([uri, usuario, senha]):
        raise ValueError(
            "Credenciais do Neo4j não encontradas no .env."
        )

    return uri, usuario, senha


def buscar_caminhos(driver) -> pd.DataFrame:
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
            AS relacoes,
        [n IN nodes(path) | n.id]
            AS nos
    """

    registros, _, _ = driver.execute_query(
        query,
        tipos=TIPOS_PERMITIDOS,
        database_="neo4j",
    )

    linhas = []

    for registro in registros:
        relacoes = list(
            registro["relacoes"]
        )

        nos = list(
            registro["nos"]
        )

        linhas.append(
            {
                "pessoa": registro["pessoa"],
                "entidade_risco": registro[
                    "entidade_risco"
                ],
                "saltos": int(
                    registro["saltos"]
                ),
                "tipo_caminho": " > ".join(
                    relacoes
                ),
                "caminho": " > ".join(
                    nos
                ),
            }
        )

    dados = pd.DataFrame(linhas)

    if dados.empty:
        raise RuntimeError(
            "Nenhum caminho foi encontrado."
        )

    dados = (
        dados.sort_values(
            [
                "pessoa",
                "entidade_risco",
                "saltos",
            ]
        )
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


def marcar_ground_truth(
    dados: pd.DataFrame,
) -> pd.DataFrame:
    """Marca os caminhos pertencentes ao ground truth."""
    resultado = dados.copy()

    resultado["relevante"] = [
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

    return resultado


def resumir_por_saltos(
    dados: pd.DataFrame,
) -> pd.DataFrame:
    """Resume desempenho por distância da entidade de risco."""
    registros = []

    for saltos, grupo in dados.groupby(
        "saltos"
    ):
        saltos_valor = int(
            pd.to_numeric(saltos)
        )
        candidatos = len(grupo)
        tp = int(
            grupo["relevante"].sum()
        )
        fp = candidatos - tp

        precision = (
            tp / candidatos
            if candidatos > 0
            else 0.0
        )

        registros.append(
            {
                "saltos": saltos_valor,
                "candidatos": candidatos,
                "tp": tp,
                "fp": fp,
                "precision": round(
                    precision,
                    4,
                ),
            }
        )

    return pd.DataFrame(registros)


def resumir_por_tipo(
    dados: pd.DataFrame,
) -> pd.DataFrame:
    """Avalia a qualidade de cada estrutura relacional."""
    resumo = (
        dados.groupby(
            "tipo_caminho"
        )
        .agg(
            candidatos=(
                "relevante",
                "size",
            ),
            tp=(
                "relevante",
                "sum",
            ),
        )
        .reset_index()
    )

    resumo["tp"] = resumo[
        "tp"
    ].astype(int)

    resumo["fp"] = (
        resumo["candidatos"]
        - resumo["tp"]
    )

    resumo["precision"] = (
        resumo["tp"]
        / resumo["candidatos"]
    ).round(4)

    resumo = resumo.sort_values(
        [
            "precision",
            "tp",
            "candidatos",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    )

    return resumo


if __name__ == "__main__":
    uri, usuario, senha = (
        carregar_configuracao()
    )

    with GraphDatabase.driver(
        uri,
        auth=(
            usuario,
            senha,
        ),
    ) as driver:
        driver.verify_connectivity()

        df_caminhos = buscar_caminhos(
            driver
        )

    df_caminhos = marcar_ground_truth(
        df_caminhos
    )

    resumo_saltos = resumir_por_saltos(
        df_caminhos
    )

    resumo_tipos = resumir_por_tipo(
        df_caminhos
    )

    ARQUIVO_SAIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_caminhos.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8",
    )

    resumo_tipos.to_csv(
        ARQUIVO_RESUMO,
        index=False,
        encoding="utf-8",
    )

    print("\nDesempenho por distância:")
    print(
        resumo_saltos.to_string(
            index=False
        )
    )

    print("\nDesempenho por tipo de caminho:")
    print(
        resumo_tipos.to_string(
            index=False
        )
    )

    print("\nExemplos de falsos positivos:")

    print(
        df_caminhos[
            ~df_caminhos["relevante"]
        ][
            [
                "pessoa",
                "entidade_risco",
                "saltos",
                "tipo_caminho",
            ]
        ]
        .head(12)
        .to_string(
            index=False
        )
    )
