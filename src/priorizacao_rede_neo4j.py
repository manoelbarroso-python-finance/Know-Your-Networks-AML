from pathlib import Path

import pandas as pd

ARQUIVO_CAMINHOS = Path(
    "data/processed/public/neo4j_analise_caminhos.csv"
)

ARQUIVO_SAIDA = Path(
    "data/processed/public/neo4j_priorizacao_rede.csv"
)

GROUND_TRUTH_TOTAL = 6

MAPA_PRIORIDADE = {
    "MATCHED_TO": 1,
    "CONTROLS > MATCHED_TO": 1,
    "USES_DEVICE > USES_DEVICE > MATCHED_TO": 2,
    "LIVES_AT > REGISTERED_AT > MATCHED_TO": 3,
    "LIVES_AT > LIVES_AT > MATCHED_TO": 4,
}

ROTULOS = {
    1: "Alta",
    2: "Média",
    3: "Baixa",
    4: "Muito baixa",
}


def carregar_dados() -> pd.DataFrame:
    """Carrega os caminhos previamente avaliados."""
    dados = pd.read_csv(
        ARQUIVO_CAMINHOS
    )

    dados["relevante"] = (
        dados["relevante"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    return dados


def classificar_prioridade(
    dados: pd.DataFrame,
) -> pd.DataFrame:
    """Classifica caminhos por força investigativa."""
    resultado = dados.copy()

    resultado["nivel"] = (
        resultado["tipo_caminho"]
        .map(MAPA_PRIORIDADE)
    )

    if resultado["nivel"].isna().any():
        desconhecidos = (
            resultado.loc[
                resultado["nivel"].isna(),
                "tipo_caminho",
            ]
            .unique()
            .tolist()
        )

        raise ValueError(
            "Tipos de caminho sem classificação: "
            f"{desconhecidos}"
        )

    resultado["nivel"] = (
        resultado["nivel"].astype(int)
    )

    resultado["prioridade"] = (
        resultado["nivel"]
        .map(ROTULOS)
    )

    return resultado


def calcular_metricas(
    dados: pd.DataFrame,
    nivel_maximo: int,
) -> dict:
    """Avalia a fila acumulada até determinado nível."""
    selecionados = dados[
        dados["nivel"] <= nivel_maximo
    ]

    candidatos = len(selecionados)

    tp = int(
        selecionados["relevante"].sum()
    )

    fp = candidatos - tp
    fn = GROUND_TRUTH_TOTAL - tp

    precision = (
        tp / candidatos
        if candidatos > 0
        else 0.0
    )

    recall = (
        tp / GROUND_TRUTH_TOTAL
        if GROUND_TRUTH_TOTAL > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "fila": (
            " + ".join(
                ROTULOS[nivel]
                for nivel in range(
                    1,
                    nivel_maximo + 1,
                )
            )
        ),
        "candidatos": candidatos,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(
            precision,
            4,
        ),
        "recall": round(
            recall,
            4,
        ),
        "f1": round(
            f1,
            4,
        ),
    }


def resumo_prioridades(
    dados: pd.DataFrame,
) -> pd.DataFrame:
    """Resume quantidade e relevância por nível."""
    resumo = (
        dados.groupby(
            [
                "nivel",
                "prioridade",
            ]
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
        .sort_values("nivel")
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

    return resumo


if __name__ == "__main__":
    df = carregar_dados()

    df = classificar_prioridade(
        df
    )

    resumo = resumo_prioridades(
        df
    )

    acumulado = pd.DataFrame(
        [
            calcular_metricas(
                df,
                nivel,
            )
            for nivel in range(1, 5)
        ]
    )

    ARQUIVO_SAIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    acumulado.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8",
    )

    print(
        "\nDesempenho por nível de prioridade:"
    )

    print(
        resumo[
            [
                "prioridade",
                "candidatos",
                "tp",
                "fp",
                "precision",
            ]
        ].to_string(
            index=False
        )
    )

    print(
        "\nDesempenho acumulado da fila investigativa:"
    )

    print(
        acumulado.to_string(
            index=False
        )
    )
