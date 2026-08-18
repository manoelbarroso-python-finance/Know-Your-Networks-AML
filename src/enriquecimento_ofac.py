from pathlib import Path

import pandas as pd

ARQUIVO_ENTIDADES = Path(
    "data/processed/private/ofac_entidades.csv"
)
ARQUIVO_ALIASES = Path(
    "data/processed/private/ofac_aliases.csv"
)
ARQUIVO_REFERENCIAS = Path(
    "data/processed/public/ofac_referencias.csv"
)

ARQUIVO_ENTIDADES_ENRIQUECIDAS = Path(
    "data/processed/private/ofac_entidades_enriquecidas.csv"
)
ARQUIVO_ALIASES_ENRIQUECIDOS = Path(
    "data/processed/private/ofac_aliases_enriquecidos.csv"
)


def carregar_dados() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Carrega os datasets preservando identificadores como texto."""
    entidades = pd.read_csv(
        ARQUIVO_ENTIDADES,
        dtype=str,
    ).fillna("")

    aliases = pd.read_csv(
        ARQUIVO_ALIASES,
        dtype=str,
    ).fillna("")

    referencias = pd.read_csv(
        ARQUIVO_REFERENCIAS,
        dtype=str,
    ).fillna("")

    return entidades, aliases, referencias


def enriquecer_entidades(
    entidades: pd.DataFrame,
    referencias: pd.DataFrame,
) -> pd.DataFrame:
    """Traduz tipos e subtipos das entidades."""
    subtipos = (
        referencias[
            referencias["grupo"] == "PartySubType"
        ][["id", "valor", "party_type_id"]]
        .rename(
            columns={
                "id": "party_subtype_id",
                "valor": "subtipo_entidade",
            }
        )
    )

    tipos = (
        referencias[
            referencias["grupo"] == "PartyType"
        ][["id", "valor"]]
        .rename(
            columns={
                "id": "party_type_id",
                "valor": "tipo_entidade",
            }
        )
    )

    resultado = entidades.merge(
        subtipos,
        on="party_subtype_id",
        how="left",
    )

    resultado = resultado.merge(
        tipos,
        on="party_type_id",
        how="left",
    )

    return resultado.fillna("")


def criar_mapa_referencias(
    referencias: pd.DataFrame,
    grupo: str,
    coluna_valor: str,
) -> dict[str, str]:
    """Cria um mapa ID → descrição para uma tabela de referência."""
    dados = referencias[
        referencias["grupo"] == grupo
    ][["id", coluna_valor]]

    return dict(
        zip(
            dados["id"],
            dados[coluna_valor],
            strict=False,
        )
    )


def traduzir_scripts(
    valor: str,
    mapa: dict[str, str],
) -> str:
    """Traduz um ou mais ScriptIDs preservando múltiplos valores."""
    if not valor:
        return ""

    ids = valor.split("|")

    traduzidos = [
        mapa.get(script_id, script_id)
        for script_id in ids
    ]

    return " | ".join(traduzidos)


def enriquecer_aliases(
    aliases: pd.DataFrame,
    referencias: pd.DataFrame,
) -> pd.DataFrame:
    """Traduz tipos de alias e sistemas de escrita."""
    mapa_alias = criar_mapa_referencias(
        referencias,
        grupo="AliasType",
        coluna_valor="valor",
    )

    mapa_script = criar_mapa_referencias(
        referencias,
        grupo="Script",
        coluna_valor="valor",
    )

    mapa_script_code = criar_mapa_referencias(
        referencias,
        grupo="Script",
        coluna_valor="script_code",
    )

    resultado = aliases.copy()

    resultado["tipo_alias"] = (
        resultado["alias_type_id"]
        .map(mapa_alias)
        .fillna("")
    )

    resultado["script"] = resultado["script_id"].apply(
        traduzir_scripts,
        mapa=mapa_script,
    )

    resultado["script_code"] = resultado["script_id"].apply(
        traduzir_scripts,
        mapa=mapa_script_code,
    )

    return resultado


def salvar_resultados(
    entidades: pd.DataFrame,
    aliases: pd.DataFrame,
) -> None:
    """Salva os datasets enriquecidos."""
    entidades.to_csv(
        ARQUIVO_ENTIDADES_ENRIQUECIDAS,
        index=False,
        encoding="utf-8",
    )

    aliases.to_csv(
        ARQUIVO_ALIASES_ENRIQUECIDOS,
        index=False,
        encoding="utf-8",
    )


if __name__ == "__main__":
    df_entidades, df_aliases, df_referencias = carregar_dados()

    entidades_enriquecidas = enriquecer_entidades(
        df_entidades,
        df_referencias,
    )

    aliases_enriquecidos = enriquecer_aliases(
        df_aliases,
        df_referencias,
    )

    salvar_resultados(
        entidades_enriquecidas,
        aliases_enriquecidos,
    )

    print("\nEntidades por tipo:")
    print(
        entidades_enriquecidas["tipo_entidade"]
        .value_counts()
        .to_string()
    )

    print("\nSubtipos de entidade:")
    print(
        entidades_enriquecidas["subtipo_entidade"]
        .value_counts()
        .to_string()
    )

    print("\nTipos de alias:")
    print(
        aliases_enriquecidos["tipo_alias"]
        .value_counts()
        .to_string()
    )

    print("\nScripts dos nomes:")
    print(
        aliases_enriquecidos["script"]
        .value_counts()
        .head(15)
        .to_string()
    )

    print(
        "\nArquivos enriquecidos salvos em "
        "data/processed/private/"
    )
