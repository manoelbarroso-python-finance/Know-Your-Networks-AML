from pathlib import Path

import numpy as np
import pandas as pd

PASTA_SAIDA = Path("data/synthetic")

ARQUIVO_TRANSACOES = (
    PASTA_SAIDA / "transacoes.csv"
)

ARQUIVO_GROUND_TRUTH = (
    PASTA_SAIDA / "ground_truth_transacoes.csv"
)

SEED = 42
N_TRANSACOES_BASE = 450

DATA_INICIAL = pd.Timestamp(
    "2026-07-01 00:00:00"
)

DIAS_SIMULADOS = 30


def carregar_contas() -> list[str]:
    """Carrega os IDs das contas sintéticas existentes."""
    contas = pd.read_csv(
        PASTA_SAIDA / "contas.csv",
        dtype=str,
    )

    return contas["account_id"].tolist()


def gerar_transacoes_base(
    contas: list[str],
    rng: np.random.Generator,
) -> list[dict]:
    """Gera movimentações normais de fundo."""
    transacoes = []

    for numero in range(
        1,
        N_TRANSACOES_BASE + 1,
    ):
        origem = str(
            rng.choice(contas)
        )

        destino = str(
            rng.choice(contas)
        )

        while destino == origem:
            destino = str(
                rng.choice(contas)
            )

        segundos = int(
            rng.integers(
                0,
                DIAS_SIMULADOS
                * 24
                * 60
                * 60,
            )
        )

        timestamp = (
            DATA_INICIAL
            + pd.Timedelta(
                seconds=segundos
            )
        )

        valor = float(
            np.clip(
                rng.lognormal(
                    mean=7.2,
                    sigma=0.9,
                ),
                50,
                25_000,
            )
        )

        transacoes.append(
            {
                "tx_id": (
                    f"TX_{numero:05d}"
                ),
                "origem": origem,
                "destino": destino,
                "valor": round(
                    valor,
                    2,
                ),
                "moeda": "USD",
                "timestamp": (
                    timestamp.isoformat()
                ),
                "ground_truth": False,
                "pattern_id": "",
            }
        )

    return transacoes


def inserir_fluxo_circular(
    transacoes: list[dict],
    contador: int,
) -> tuple[int, dict]:
    """Insere um fluxo circular conhecido."""
    movimentos = [
        (
            "ACCOUNT_010",
            "ACCOUNT_011",
            8_500.00,
            "2026-07-15T10:00:00",
        ),
        (
            "ACCOUNT_011",
            "ACCOUNT_012",
            8_300.00,
            "2026-07-15T11:20:00",
        ),
        (
            "ACCOUNT_012",
            "ACCOUNT_010",
            8_100.00,
            "2026-07-15T13:00:00",
        ),
    ]

    for origem, destino, valor, timestamp in movimentos:
        contador += 1

        transacoes.append(
            {
                "tx_id": (
                    f"TX_{contador:05d}"
                ),
                "origem": origem,
                "destino": destino,
                "valor": valor,
                "moeda": "USD",
                "timestamp": timestamp,
                "ground_truth": True,
                "pattern_id": "GT_TX_001",
            }
        )

    ground_truth = {
        "pattern_id": "GT_TX_001",
        "tipo": "Fluxo circular",
        "descricao": (
            "ACCOUNT_010 transfere para ACCOUNT_011, "
            "que transfere para ACCOUNT_012, "
            "com retorno posterior a ACCOUNT_010."
        ),
        "contas": (
            "ACCOUNT_010 > ACCOUNT_011 > "
            "ACCOUNT_012 > ACCOUNT_010"
        ),
    }

    return contador, ground_truth


def inserir_concentracao_repasse(
    transacoes: list[dict],
    contador: int,
) -> tuple[int, dict]:
    """Insere concentração seguida de repasse rápido."""
    entradas = [
        (
            "ACCOUNT_020",
            2_800.00,
            "2026-07-20T09:00:00",
        ),
        (
            "ACCOUNT_021",
            3_100.00,
            "2026-07-20T09:18:00",
        ),
        (
            "ACCOUNT_022",
            2_600.00,
            "2026-07-20T09:37:00",
        ),
        (
            "ACCOUNT_023",
            3_000.00,
            "2026-07-20T09:55:00",
        ),
    ]

    for origem, valor, timestamp in entradas:
        contador += 1

        transacoes.append(
            {
                "tx_id": (
                    f"TX_{contador:05d}"
                ),
                "origem": origem,
                "destino": "ACCOUNT_005",
                "valor": valor,
                "moeda": "USD",
                "timestamp": timestamp,
                "ground_truth": True,
                "pattern_id": "GT_TX_002",
            }
        )

    contador += 1

    transacoes.append(
        {
            "tx_id": (
                f"TX_{contador:05d}"
            ),
            "origem": "ACCOUNT_005",
            "destino": "ACCOUNT_105",
            "valor": 10_700.00,
            "moeda": "USD",
            "timestamp": (
                "2026-07-20T10:35:00"
            ),
            "ground_truth": True,
            "pattern_id": "GT_TX_002",
        }
    )

    ground_truth = {
        "pattern_id": "GT_TX_002",
        "tipo": (
            "Concentração e repasse rápido"
        ),
        "descricao": (
            "Quatro contas concentram recursos em "
            "ACCOUNT_005, que realiza repasse "
            "subsequente para ACCOUNT_105."
        ),
        "contas": (
            "ACCOUNT_020/021/022/023 > "
            "ACCOUNT_005 > ACCOUNT_105"
        ),
    }

    return contador, ground_truth


def validar_transacoes(
    transacoes: pd.DataFrame,
    contas_validas: set[str],
) -> None:
    """Executa validações básicas do dataset."""
    if transacoes["tx_id"].duplicated().any():
        raise ValueError(
            "Existem IDs de transação duplicados."
        )

    if not set(
        transacoes["origem"]
    ).issubset(contas_validas):
        raise ValueError(
            "Há contas de origem inexistentes."
        )

    if not set(
        transacoes["destino"]
    ).issubset(contas_validas):
        raise ValueError(
            "Há contas de destino inexistentes."
        )

    if (
        transacoes["valor"] <= 0
    ).any():
        raise ValueError(
            "Foram encontrados valores não positivos."
        )

    if (
        transacoes["origem"]
        == transacoes["destino"]
    ).any():
        raise ValueError(
            "Há transferência para a própria conta."
        )


if __name__ == "__main__":
    rng = np.random.default_rng(
        SEED
    )

    ids_contas = carregar_contas()

    transacoes = gerar_transacoes_base(
        ids_contas,
        rng,
    )

    contador_tx = len(
        transacoes
    )

    ground_truth = []

    contador_tx, gt_ciclo = (
        inserir_fluxo_circular(
            transacoes,
            contador_tx,
        )
    )

    ground_truth.append(
        gt_ciclo
    )

    contador_tx, gt_concentracao = (
        inserir_concentracao_repasse(
            transacoes,
            contador_tx,
        )
    )

    ground_truth.append(
        gt_concentracao
    )

    df_transacoes = pd.DataFrame(
        transacoes
    )

    df_transacoes["timestamp"] = (
        pd.to_datetime(
            df_transacoes["timestamp"]
        )
    )

    df_transacoes = (
        df_transacoes.sort_values(
            "timestamp"
        )
        .reset_index(drop=True)
    )

    validar_transacoes(
        df_transacoes,
        set(ids_contas),
    )

    df_ground_truth = pd.DataFrame(
        ground_truth
    )

    PASTA_SAIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_transacoes.to_csv(
        ARQUIVO_TRANSACOES,
        index=False,
        encoding="utf-8",
    )

    df_ground_truth.to_csv(
        ARQUIVO_GROUND_TRUTH,
        index=False,
        encoding="utf-8",
    )

    print("\nTransações sintéticas geradas.")

    print(
        f"Transações de fundo: "
        f"{N_TRANSACOES_BASE:,}"
    )

    print(
        f"Transações de ground truth: "
        f"{int(df_transacoes['ground_truth'].sum()):,}"
    )

    print(
        f"Total de transações: "
        f"{len(df_transacoes):,}"
    )

    print("\nPadrões inseridos:")

    print(
        df_ground_truth[
            [
                "pattern_id",
                "tipo",
            ]
        ].to_string(
            index=False
        )
    )

    print(
        "\nArquivos salvos em data/synthetic/"
    )
