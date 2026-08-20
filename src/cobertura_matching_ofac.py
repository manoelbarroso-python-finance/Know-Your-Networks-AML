from pathlib import Path

import pandas as pd

ARQUIVO_ENTIDADES = Path(
    "data/processed/private/ofac_entidades_enriquecidas.csv"
)

ARQUIVO_ATRIBUTOS = Path(
    "data/processed/private/ofac_atributos_identidade.csv"
)

ARQUIVO_SAIDA = Path(
    "data/processed/public/ofac_cobertura_por_tipo.csv"
)

CAMPOS = [
    "data_nascimento",
    "local_nascimento",
    "nacionalidade",
    "cidadania",
    "genero",
]


def carregar_dados() -> pd.DataFrame:
    """Combina atributos de identidade com o tipo de entidade."""
    entidades = pd.read_csv(
        ARQUIVO_ENTIDADES,
        dtype=str,
    ).fillna("")

    atributos = pd.read_csv(
        ARQUIVO_ATRIBUTOS,
        dtype=str,
    ).fillna("")

    return atributos.merge(
        entidades[
            [
                "ofac_id",
                "tipo_entidade",
            ]
        ],
        on="ofac_id",
        how="left",
    )


def calcular_cobertura(
    dados: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula cobertura dos atributos por tipo de entidade."""
    resultados = []

    for tipo, grupo in dados.groupby("tipo_entidade"):
        total = len(grupo)

        for campo in CAMPOS:
            quantidade = grupo[campo].ne("").sum()

            resultados.append(
                {
                    "tipo_entidade": tipo,
                    "atributo": campo,
                    "entidades_com_informacao": int(quantidade),
                    "total_entidades": total,
                    "cobertura_pct": round(
                        quantidade / total * 100,
                        2,
                    ),
                }
            )

    return pd.DataFrame(resultados)


if __name__ == "__main__":
    df_dados = carregar_dados()
    df_cobertura = calcular_cobertura(df_dados)

    ARQUIVO_SAIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_cobertura.to_csv(
        ARQUIVO_SAIDA,
        index=False,
    )

    for tipo in df_cobertura["tipo_entidade"].unique():
        print(f"\n=== {tipo} ===")

        print(
            df_cobertura[
                df_cobertura["tipo_entidade"] == tipo
            ][
                [
                    "atributo",
                    "entidades_com_informacao",
                    "total_entidades",
                    "cobertura_pct",
                ]
            ].to_string(index=False)
        )

    print(f"\nArquivo salvo em: {ARQUIVO_SAIDA}")
