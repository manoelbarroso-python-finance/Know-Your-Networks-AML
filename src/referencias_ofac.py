from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")
ARQUIVO_SAIDA = Path(
    "data/processed/public/ofac_referencias.csv"
)

GRUPOS = {
    "PartyTypeValues": "PartyType",
    "PartySubTypeValues": "PartySubType",
    "AliasTypeValues": "AliasType",
    "FeatureTypeValues": "FeatureType",
    "NamePartTypeValues": "NamePartType",
    "ScriptValues": "Script",
    "SanctionsProgramValues": "SanctionsProgram",
    "IDRegDocTypeValues": "IDRegDocType",
    "CountryValues": "Country",
}


def nome_local(tag: str) -> str:
    """Remove o namespace XML."""
    return tag.rsplit("}", 1)[-1]


def texto_limpo(texto: str | None) -> str:
    """Remove espaços excedentes."""
    if not texto:
        return ""

    return " ".join(texto.split())


def extrair_referencias(caminho: Path) -> pd.DataFrame:
    """Extrai tabelas de referência selecionadas do XML da OFAC."""
    registros = []
    grupo_atual = None

    contexto = ET.iterparse(
        caminho,
        events=("start", "end"),
    )

    for evento, elemento in contexto:
        tag = nome_local(elemento.tag)

        if evento == "start" and tag in GRUPOS:
            grupo_atual = tag
            continue

        if evento != "end" or grupo_atual is None:
            continue

        if tag == grupo_atual:
            grupo_atual = None
            elemento.clear()
            continue

        if tag != GRUPOS[grupo_atual]:
            continue

        registros.append(
            {
                "grupo": tag,
                "id": elemento.attrib.get("ID", ""),
                "valor": texto_limpo(elemento.text),
                "party_type_id": elemento.attrib.get(
                    "PartyTypeID",
                    "",
                ),
                "feature_type_group_id": elemento.attrib.get(
                    "FeatureTypeGroupID",
                    "",
                ),
                "script_code": elemento.attrib.get(
                    "ScriptCode",
                    "",
                ),
            }
        )

        elemento.clear()

    return pd.DataFrame(registros)


def salvar_referencias(referencias: pd.DataFrame) -> None:
    """Salva referências públicas em formato tabular."""
    ARQUIVO_SAIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    referencias.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8",
    )


if __name__ == "__main__":
    df_referencias = extrair_referencias(ARQUIVO_OFAC)
    salvar_referencias(df_referencias)

    print(f"Referências extraídas: {len(df_referencias):,}")

    print("\nRegistros por grupo:")
    print(
        df_referencias["grupo"]
        .value_counts()
        .to_string()
    )

    print(f"\nArquivo salvo em: {ARQUIVO_SAIDA}")
