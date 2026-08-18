from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ARQUIVO_ENTIDADES = Path(
    "data/processed/private/ofac_entidades_enriquecidas.csv"
)
ARQUIVO_ALIASES = Path(
    "data/processed/private/ofac_aliases_enriquecidos.csv"
)

PASTA_PUBLICA = Path("data/processed/public")
PASTA_FIGURAS = Path("reports/figures")


def converter_booleano(serie: pd.Series) -> pd.Series:
    """Converte booleanos armazenados como texto."""
    return serie.astype(str).str.lower().eq("true")


def preparar_dados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega entidades e aliases e combina o tipo de entidade."""
    entidades = pd.read_csv(
        ARQUIVO_ENTIDADES,
        dtype=str,
    ).fillna("")

    aliases = pd.read_csv(
        ARQUIVO_ALIASES,
        dtype=str,
    ).fillna("")

    aliases["primary"] = converter_booleano(aliases["primary"])
    aliases["low_quality"] = converter_booleano(
        aliases["low_quality"]
    )

    aliases = aliases.merge(
        entidades[["ofac_id", "tipo_entidade"]],
        on="ofac_id",
        how="left",
    )

    return entidades, aliases


def calcular_metricas(
    entidades: pd.DataFrame,
    aliases: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas de complexidade nominal por tipo de entidade."""
    nomes_por_entidade = (
        aliases.groupby(["ofac_id", "tipo_entidade"])
        .size()
        .rename("quantidade_nomes")
        .reset_index()
    )

    resumo = (
        nomes_por_entidade.groupby("tipo_entidade")
        .agg(
            entidades=("ofac_id", "nunique"),
            media_nomes=("quantidade_nomes", "mean"),
            mediana_nomes=("quantidade_nomes", "median"),
            max_nomes=("quantidade_nomes", "max"),
        )
        .reset_index()
    )

    resumo["media_nomes"] = resumo["media_nomes"].round(2)

    return resumo


def calcular_qualidade_aliases(
    aliases: pd.DataFrame,
) -> pd.DataFrame:
    """Resume aliases fortes e fracos por tipo de entidade."""
    aliases_secundarios = aliases[~aliases["primary"]].copy()

    aliases_secundarios["qualidade"] = aliases_secundarios[
        "low_quality"
    ].map(
        {
            False: "Forte",
            True: "Fraco",
        }
    )

    resumo = (
        aliases_secundarios.groupby(
            ["tipo_entidade", "qualidade"]
        )
        .size()
        .rename("quantidade")
        .reset_index()
    )

    return resumo


def salvar_resultados(
    metricas: pd.DataFrame,
    qualidade: pd.DataFrame,
) -> None:
    """Salva tabelas agregadas e figura exploratória."""
    PASTA_PUBLICA.mkdir(parents=True, exist_ok=True)
    PASTA_FIGURAS.mkdir(parents=True, exist_ok=True)

    metricas.to_csv(
        PASTA_PUBLICA / "ofac_complexidade_nominal.csv",
        index=False,
    )

    qualidade.to_csv(
        PASTA_PUBLICA / "ofac_qualidade_aliases.csv",
        index=False,
    )

    dados_grafico = metricas.sort_values(
        "media_nomes",
        ascending=True,
    )

    plt.figure(figsize=(8, 5))

    plt.barh(
        dados_grafico["tipo_entidade"],
        dados_grafico["media_nomes"],
    )

    plt.xlabel("Média de nomes documentados por entidade")
    plt.title("Complexidade nominal por tipo de entidade — OFAC SDN")
    plt.tight_layout()

    plt.savefig(
        PASTA_FIGURAS / "ofac_complexidade_nominal.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()


if __name__ == "__main__":
    df_entidades, df_aliases = preparar_dados()

    df_metricas = calcular_metricas(
        df_entidades,
        df_aliases,
    )

    df_qualidade = calcular_qualidade_aliases(
        df_aliases,
    )

    salvar_resultados(
        df_metricas,
        df_qualidade,
    )

    print("\nComplexidade nominal:")
    print(df_metricas.to_string(index=False))

    print("\nQualidade dos aliases:")
    print(df_qualidade.to_string(index=False))

    print(
        "\nFigura salva em: "
        "reports/figures/ofac_complexidade_nominal.png"
    )
