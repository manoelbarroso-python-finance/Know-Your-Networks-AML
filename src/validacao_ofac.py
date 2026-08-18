from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ARQUIVO_ENTIDADES = Path(
    "data/processed/private/ofac_entidades.csv"
)
ARQUIVO_ALIASES = Path(
    "data/processed/private/ofac_aliases.csv"
)

PASTA_PUBLICA = Path("data/processed/public")
PASTA_FIGURAS = Path("reports/figures")


def converter_booleano(serie: pd.Series) -> pd.Series:
    """Converte valores True/False provenientes do CSV."""
    return serie.astype(str).str.lower().eq("true")


def gerar_resumo() -> tuple[pd.DataFrame, pd.Series]:
    """Valida os datasets processados e calcula métricas iniciais."""
    entidades = pd.read_csv(ARQUIVO_ENTIDADES)
    aliases = pd.read_csv(ARQUIVO_ALIASES)

    primary = converter_booleano(aliases["primary"])
    low_quality = converter_booleano(aliases["low_quality"])

    categorias_alias = pd.Series(
        {
            "Nome principal": int(primary.sum()),
            "Alias forte": int((~primary & ~low_quality).sum()),
            "Alias fraco": int((~primary & low_quality).sum()),
        }
    )

    resumo = pd.DataFrame(
        {
            "metrica": [
                "Entidades",
                "Nomes e aliases",
                "Entidades com ID duplicado",
                "Entidades sem nome principal",
                "Nomes vazios",
                "Média de nomes por entidade",
            ],
            "valor": [
                len(entidades),
                len(aliases),
                int(entidades["ofac_id"].duplicated().sum()),
                int(entidades["nome_principal"].isna().sum()),
                int(aliases["nome_original"].isna().sum()),
                round(len(aliases) / len(entidades), 2),
            ],
        }
    )

    return resumo, categorias_alias


def salvar_resultados(
    resumo: pd.DataFrame,
    categorias_alias: pd.Series,
) -> None:
    """Salva métricas agregadas e a primeira figura da análise."""
    PASTA_PUBLICA.mkdir(parents=True, exist_ok=True)
    PASTA_FIGURAS.mkdir(parents=True, exist_ok=True)

    resumo.to_csv(
        PASTA_PUBLICA / "ofac_resumo.csv",
        index=False,
    )

    plt.figure(figsize=(8, 5))
    plt.bar(
        categorias_alias.index,
        categorias_alias.values,
    )

    plt.title("Composição dos nomes e aliases na OFAC SDN")
    plt.ylabel("Quantidade de registros")
    plt.tight_layout()

    plt.savefig(
        PASTA_FIGURAS / "ofac_composicao_aliases.png",
        dpi=180,
    )

    plt.close()


if __name__ == "__main__":
    df_resumo, aliases_por_categoria = gerar_resumo()

    salvar_resultados(
        df_resumo,
        aliases_por_categoria,
    )

    print("\nResumo da OFAC:")
    print(df_resumo.to_string(index=False))

    print("\nClassificação dos nomes:")
    print(aliases_por_categoria.to_string())

    print(
        "\nFigura salva em: "
        "reports/figures/ofac_composicao_aliases.png"
    )
