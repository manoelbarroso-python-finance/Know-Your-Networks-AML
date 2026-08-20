from pathlib import Path

import pandas as pd

ARQUIVO_ENTIDADES = Path(
    "data/processed/private/ofac_entidades_enriquecidas.csv"
)
ARQUIVO_ALIASES = Path(
    "data/processed/private/ofac_aliases_enriquecidos.csv"
)

ARQUIVO_BENCHMARK = Path(
    "data/processed/private/ofac_benchmark_matching.csv"
)


def converter_booleano(serie: pd.Series) -> pd.Series:
    """Converte valores booleanos armazenados como texto."""
    return serie.astype(str).str.lower().eq("true")


def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega entidades e aliases enriquecidos."""
    entidades = pd.read_csv(
        ARQUIVO_ENTIDADES,
        dtype=str,
    ).fillna("")

    aliases = pd.read_csv(
        ARQUIVO_ALIASES,
        dtype=str,
    ).fillna("")

    aliases["primary"] = converter_booleano(
        aliases["primary"]
    )

    aliases["low_quality"] = converter_booleano(
        aliases["low_quality"]
    )

    return entidades, aliases


def criar_pares_positivos(
    entidades: pd.DataFrame,
    aliases: pd.DataFrame,
) -> pd.DataFrame:
    """Cria pares de nomes pertencentes à mesma entidade OFAC."""
    base = aliases.merge(
        entidades[
            [
                "ofac_id",
                "tipo_entidade",
                "nome_principal",
                "nome_principal_normalizado",
            ]
        ],
        on="ofac_id",
        how="inner",
    )

    positivos = base[
        (~base["primary"])
        & (base["nome_normalizado"] != "")
        & (
            base["nome_normalizado"]
            != base["nome_principal_normalizado"]
        )
    ].copy()

    positivos = positivos[
        [
            "ofac_id",
            "tipo_entidade",
            "nome_principal",
            "nome_principal_normalizado",
            "nome_original",
            "nome_normalizado",
            "tipo_alias",
            "low_quality",
            "script",
        ]
    ]

    positivos = positivos.rename(
        columns={
            "nome_principal": "nome_a",
            "nome_principal_normalizado": "nome_a_normalizado",
            "nome_original": "nome_b",
            "nome_normalizado": "nome_b_normalizado",
        }
    )

    positivos["match_real"] = True

    return positivos


def salvar_benchmark(
    benchmark: pd.DataFrame,
) -> None:
    """Salva o benchmark privado de matching."""
    benchmark.to_csv(
        ARQUIVO_BENCHMARK,
        index=False,
        encoding="utf-8",
    )


if __name__ == "__main__":
    df_entidades, df_aliases = carregar_dados()

    benchmark_positivo = criar_pares_positivos(
        df_entidades,
        df_aliases,
    )

    salvar_benchmark(benchmark_positivo)

    print("\nBenchmark positivo — OFAC")

    print(f"Pares positivos: {len(benchmark_positivo):,}")

    print("\nPor tipo de entidade:")
    print(
        benchmark_positivo["tipo_entidade"]
        .value_counts()
        .to_string()
    )

    print("\nPor qualidade do alias:")
    print(
        benchmark_positivo["low_quality"]
        .value_counts()
        .rename(
            index={
                False: "Forte",
                True: "Fraco",
            }
        )
        .to_string()
    )

    print("\nScripts:")
    print(
        benchmark_positivo["script"]
        .value_counts()
        .head(10)
        .to_string()
    )

    print(f"\nArquivo salvo em: {ARQUIVO_BENCHMARK}")
