from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

from src.analise_caminhos_neo4j import (
    buscar_caminhos,
    carregar_configuracao,
    marcar_ground_truth,
)

ARQUIVO_DETALHE = Path(
    "data/processed/public/neo4j_exclusividade_caminhos.csv"
)

ARQUIVO_RESUMO = Path(
    "data/processed/public/neo4j_resumo_exclusividade.csv"
)


def extrair_intermediarios(
    caminho: str,
) -> list[str]:
    """Extrai nós intermediários de um caminho."""
    nos = [
        item.strip()
        for item in caminho.split(">")
    ]

    if len(nos) <= 2:
        return []

    return nos[1:-1]


def buscar_graus(
    driver,
    ids: list[str],
) -> dict[str, dict]:
    """Obtém grau e tipo dos nós intermediários."""
    ids_unicos = sorted(set(ids))

    if not ids_unicos:
        return {}

    query = """
    UNWIND $ids AS node_id

    MATCH (n {id: node_id})

    OPTIONAL MATCH (n)--(vizinho)

    RETURN
        node_id,
        labels(n) AS labels,
        count(vizinho) AS grau
    """

    registros, _, _ = driver.execute_query(
        query,
        ids=ids_unicos,
        database_="neo4j",
    )

    return {
        str(registro["node_id"]): {
            "labels": " | ".join(
                str(label)
                for label in registro["labels"]
            ),
            "grau": int(registro["grau"]),
        }
        for registro in registros
    }


def adicionar_exclusividade(
    caminhos: pd.DataFrame,
    graus: dict[str, dict],
) -> pd.DataFrame:
    """Acrescenta medidas estruturais dos intermediários."""
    registros = []

    for _, linha in caminhos.iterrows():
        intermediarios = extrair_intermediarios(
            linha["caminho"]
        )

        graus_intermediarios = [
            int(
                graus.get(
                    node_id,
                    {},
                ).get(
                    "grau",
                    0,
                )
            )
            for node_id in intermediarios
        ]

        tipos_intermediarios = [
            str(
                graus.get(
                    node_id,
                    {},
                ).get(
                    "labels",
                    "",
                )
            )
            for node_id in intermediarios
        ]

        if graus_intermediarios:
            grau_maximo = max(
                graus_intermediarios
            )

            grau_medio = sum(
                graus_intermediarios
            ) / len(
                graus_intermediarios
            )

            exclusividade = (
                1 / grau_maximo
                if grau_maximo > 0
                else 0.0
            )
        else:
            grau_maximo = 0
            grau_medio = 0.0
            exclusividade = 1.0

        registro = linha.to_dict()

        registro[
            "intermediarios"
        ] = " > ".join(
            intermediarios
        )

        registro[
            "tipos_intermediarios"
        ] = " > ".join(
            tipos_intermediarios
        )

        registro[
            "grau_max_intermediario"
        ] = grau_maximo

        registro[
            "grau_medio_intermediario"
        ] = round(
            grau_medio,
            3,
        )

        registro[
            "exclusividade"
        ] = round(
            exclusividade,
            4,
        )

        registros.append(
            registro
        )

    return pd.DataFrame(
        registros
    )


def gerar_resumo(
    dados: pd.DataFrame,
) -> pd.DataFrame:
    """Compara exclusividade entre caminhos verdadeiros e ruído."""
    resumo = (
        dados.groupby(
            [
                "tipo_caminho",
                "relevante",
            ]
        )
        .agg(
            candidatos=(
                "pessoa",
                "size",
            ),
            grau_medio=(
                "grau_medio_intermediario",
                "mean",
            ),
            grau_max_medio=(
                "grau_max_intermediario",
                "mean",
            ),
            exclusividade_media=(
                "exclusividade",
                "mean",
            ),
        )
        .reset_index()
    )

    resumo[
        "grau_medio"
    ] = resumo[
        "grau_medio"
    ].round(3)

    resumo[
        "grau_max_medio"
    ] = resumo[
        "grau_max_medio"
    ].round(3)

    resumo[
        "exclusividade_media"
    ] = resumo[
        "exclusividade_media"
    ].round(4)

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

        todos_intermediarios = []

        for caminho in df_caminhos[
            "caminho"
        ]:
            todos_intermediarios.extend(
                extrair_intermediarios(
                    caminho
                )
            )

        mapa_graus = buscar_graus(
            driver,
            todos_intermediarios,
        )

    df_exclusividade = (
        adicionar_exclusividade(
            df_caminhos,
            mapa_graus,
        )
    )

    df_resumo = gerar_resumo(
        df_exclusividade
    )

    ARQUIVO_DETALHE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_exclusividade.to_csv(
        ARQUIVO_DETALHE,
        index=False,
        encoding="utf-8",
    )

    df_resumo.to_csv(
        ARQUIVO_RESUMO,
        index=False,
        encoding="utf-8",
    )

    print(
        "\nExclusividade por tipo de caminho "
        "e relevância:"
    )

    print(
        df_resumo.to_string(
            index=False
        )
    )

    print(
        "\nCasos relevantes de três saltos:"
    )

    print(
        df_exclusividade[
            df_exclusividade["relevante"]
            & df_exclusividade["saltos"].eq(3)
        ][
            [
                "pessoa",
                "entidade_risco",
                "tipo_caminho",
                "intermediarios",
                "grau_max_intermediario",
                "exclusividade",
            ]
        ].to_string(
            index=False
        )
    )

    print(
        "\nFalsos positivos de menor exclusividade:"
    )

    print(
        df_exclusividade[
            ~df_exclusividade["relevante"]
        ][
            [
                "pessoa",
                "entidade_risco",
                "tipo_caminho",
                "grau_max_intermediario",
                "exclusividade",
            ]
        ]
        .sort_values(
            "exclusividade"
        )
        .head(12)
        .to_string(
            index=False
        )
    )
