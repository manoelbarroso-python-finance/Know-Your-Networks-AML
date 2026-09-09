from pathlib import Path

import pandas as pd

PASTA_DADOS = Path("data/synthetic")

ARQUIVOS_NOS = {
    "Person": ("pessoas.csv", "person_id"),
    "Company": ("empresas.csv", "company_id"),
    "Account": ("contas.csv", "account_id"),
    "Device": ("dispositivos.csv", "device_id"),
    "Address": ("enderecos.csv", "address_id"),
    "RiskEntity": ("entidades_risco.csv", "risk_id"),
}

RELACOES_ESPERADAS = {
    "OWNS",
    "USES_DEVICE",
    "LIVES_AT",
    "REGISTERED_AT",
    "CONTROLS",
    "MATCHED_TO",
}


def carregar_ids() -> tuple[set[str], dict[str, int]]:
    """Carrega e valida os identificadores de todos os nós."""
    todos_ids = set()
    contagens = {}

    for label, (arquivo, coluna_id) in ARQUIVOS_NOS.items():
        dados = pd.read_csv(
            PASTA_DADOS / arquivo,
            dtype=str,
        ).fillna("")

        ids = dados[coluna_id]

        if ids.duplicated().any():
            raise ValueError(
                f"IDs duplicados encontrados em {arquivo}."
            )

        conjunto = set(ids)

        if todos_ids.intersection(conjunto):
            raise ValueError(
                f"IDs reutilizados entre tipos de nós: {label}."
            )

        todos_ids.update(conjunto)
        contagens[label] = len(dados)

    return todos_ids, contagens


def validar_relacoes(
    todos_ids: set[str],
) -> pd.DataFrame:
    """Valida endpoints e tipos dos relacionamentos."""
    relacoes = pd.read_csv(
        PASTA_DADOS / "relacoes.csv",
        dtype=str,
    ).fillna("")

    origens_invalidas = ~relacoes["origem"].isin(todos_ids)
    destinos_invalidos = ~relacoes["destino"].isin(todos_ids)

    if origens_invalidas.any():
        raise ValueError(
            "Há relacionamentos com origem inexistente."
        )

    if destinos_invalidos.any():
        raise ValueError(
            "Há relacionamentos com destino inexistente."
        )

    tipos_encontrados = set(
        relacoes["tipo"].unique()
    )

    tipos_inesperados = (
        tipos_encontrados - RELACOES_ESPERADAS
    )

    if tipos_inesperados:
        raise ValueError(
            "Tipos de relacionamento inesperados: "
            f"{sorted(tipos_inesperados)}"
        )

    return relacoes


def existe_relacao(
    relacoes: pd.DataFrame,
    origem: str,
    destino: str,
    tipo: str,
) -> bool:
    """Verifica a existência de uma relação específica."""
    return bool(
        (
            relacoes["origem"].eq(origem)
            & relacoes["destino"].eq(destino)
            & relacoes["tipo"].eq(tipo)
        ).any()
    )


def validar_ground_truth(
    relacoes: pd.DataFrame,
) -> None:
    """Confirma os padrões investigativos plantados."""
    verificacoes = {
        "GT_001": existe_relacao(
            relacoes,
            "PERSON_001",
            "RISK_001",
            "MATCHED_TO",
        ),
        "GT_002": (
            existe_relacao(
                relacoes,
                "PERSON_002",
                "COMPANY_001",
                "CONTROLS",
            )
            and existe_relacao(
                relacoes,
                "COMPANY_001",
                "RISK_002",
                "MATCHED_TO",
            )
        ),
        "GT_003": all(
            existe_relacao(
                relacoes,
                person_id,
                "DEVICE_001",
                "USES_DEVICE",
            )
            for person_id in [
                "PERSON_003",
                "PERSON_004",
                "PERSON_005",
            ]
        )
        and existe_relacao(
            relacoes,
            "PERSON_005",
            "RISK_003",
            "MATCHED_TO",
        ),
        "GT_004": (
            existe_relacao(
                relacoes,
                "PERSON_006",
                "ADDRESS_001",
                "LIVES_AT",
            )
            and existe_relacao(
                relacoes,
                "COMPANY_002",
                "ADDRESS_001",
                "REGISTERED_AT",
            )
            and existe_relacao(
                relacoes,
                "COMPANY_002",
                "RISK_004",
                "MATCHED_TO",
            )
        ),
        "GT_005": all(
            existe_relacao(
                relacoes,
                person_id,
                "ADDRESS_035",
                "LIVES_AT",
            )
            for person_id in [
                "PERSON_020",
                "PERSON_021",
                "PERSON_022",
                "PERSON_023",
                "PERSON_024",
                "PERSON_025",
            ]
        ),
    }

    falhas = [
        pattern_id
        for pattern_id, valido in verificacoes.items()
        if not valido
    ]

    if falhas:
        raise ValueError(
            "Ground truth incompleto: "
            f"{', '.join(falhas)}"
        )

    print("\nGround truth validado:")

    for pattern_id in verificacoes:
        print(f"- {pattern_id}: OK")


if __name__ == "__main__":
    ids, contagens_nos = carregar_ids()

    df_relacoes = validar_relacoes(ids)

    validar_ground_truth(df_relacoes)

    print("\nNós por tipo:")
    for tipo, quantidade in contagens_nos.items():
        print(f"{tipo:<12} {quantidade:>4}")

    print(f"\nTotal de nós: {len(ids):,}")

    print("\nRelacionamentos por tipo:")
    print(
        df_relacoes["tipo"]
        .value_counts()
        .to_string()
    )

    print(
        f"\nTotal de relacionamentos: "
        f"{len(df_relacoes):,}"
    )

    print(
        "\nValidação estrutural concluída com sucesso."
    )
