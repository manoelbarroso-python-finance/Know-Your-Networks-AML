from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")

ARQUIVO_ENTIDADES = Path(
    "data/processed/private/ofac_entidades_enriquecidas.csv"
)

ARQUIVO_REFERENCIAS = Path(
    "data/processed/public/ofac_referencias.csv"
)

ARQUIVO_DOCUMENTOS = Path(
    "data/processed/private/ofac_documentos.csv"
)

ARQUIVO_COBERTURA = Path(
    "data/processed/public/ofac_cobertura_documentos.csv"
)


def nome_local(tag: str) -> str:
    """Remove o namespace XML."""
    return tag.rsplit("}", 1)[-1]


def texto_limpo(texto: str | None) -> str:
    """Remove espaços excedentes."""
    if not texto:
        return ""

    return " ".join(texto.split())


def carregar_mapas() -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    """Cria mapas para identidade, tipo de entidade e documento."""
    entidades = pd.read_csv(
        ARQUIVO_ENTIDADES,
        dtype=str,
    ).fillna("")

    referencias = pd.read_csv(
        ARQUIVO_REFERENCIAS,
        dtype=str,
    ).fillna("")

    identity_to_ofac = dict(
        zip(
            entidades["identity_id"],
            entidades["ofac_id"],
            strict=False,
        )
    )

    ofac_to_tipo = dict(
        zip(
            entidades["ofac_id"],
            entidades["tipo_entidade"],
            strict=False,
        )
    )

    tipos_documento = referencias[
        referencias["grupo"] == "IDRegDocType"
    ]

    doc_type_map = dict(
        zip(
            tipos_documento["id"],
            tipos_documento["valor"],
            strict=False,
        )
    )

    return identity_to_ofac, ofac_to_tipo, doc_type_map


def extrair_documentos(
    caminho: Path,
    identity_to_ofac: dict[str, str],
    ofac_to_tipo: dict[str, str],
    doc_type_map: dict[str, str],
) -> pd.DataFrame:
    """Extrai documentos oficiais associados às entidades OFAC."""
    registros = []

    contexto = ET.iterparse(
        caminho,
        events=("end",),
    )

    for _, elemento in contexto:
        if nome_local(elemento.tag) != "IDRegDocument":
            continue

        identity_id = elemento.attrib.get("IdentityID", "")
        ofac_id = identity_to_ofac.get(identity_id, "")

        tipo_id = elemento.attrib.get("IDRegDocTypeID", "")

        numero = ""

        for item in elemento.iter():
            if nome_local(item.tag) == "IDRegistrationNo":
                numero = texto_limpo(item.text)
                break

        registros.append(
            {
                "documento_id": elemento.attrib.get("ID", ""),
                "ofac_id": ofac_id,
                "identity_id": identity_id,
                "tipo_entidade": ofac_to_tipo.get(ofac_id, ""),
                "tipo_documento_id": tipo_id,
                "tipo_documento": doc_type_map.get(
                    tipo_id,
                    "",
                ),
                "numero_documento": numero,
                "pais_emissor_id": elemento.attrib.get(
                    "IssuedBy-CountryID",
                    "",
                ),
                "validity_id": elemento.attrib.get(
                    "ValidityID",
                    "",
                ),
            }
        )

        elemento.clear()

    return pd.DataFrame(registros)


def calcular_cobertura(
    documentos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula cobertura documental por tipo de entidade."""
    entidades = pd.read_csv(
        ARQUIVO_ENTIDADES,
        dtype=str,
    ).fillna("")

    resultados = []

    for tipo, grupo in entidades.groupby("tipo_entidade"):
        total = len(grupo)

        ids_com_documento = documentos.loc[
            documentos["tipo_entidade"] == tipo,
            "ofac_id",
        ].nunique()

        resultados.append(
            {
                "tipo_entidade": tipo,
                "entidades_com_documento": int(
                    ids_com_documento
                ),
                "total_entidades": total,
                "cobertura_pct": round(
                    ids_com_documento / total * 100,
                    2,
                ),
            }
        )

    return pd.DataFrame(resultados)


def salvar_resultados(
    documentos: pd.DataFrame,
    cobertura: pd.DataFrame,
) -> None:
    """Salva documentos privados e métricas agregadas públicas."""
    ARQUIVO_DOCUMENTOS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARQUIVO_COBERTURA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    documentos.to_csv(
        ARQUIVO_DOCUMENTOS,
        index=False,
        encoding="utf-8",
    )

    cobertura.to_csv(
        ARQUIVO_COBERTURA,
        index=False,
        encoding="utf-8",
    )


if __name__ == "__main__":
    mapa_identidade, mapa_tipo, mapa_documento = (
        carregar_mapas()
    )

    df_documentos = extrair_documentos(
        ARQUIVO_OFAC,
        mapa_identidade,
        mapa_tipo,
        mapa_documento,
    )

    df_cobertura = calcular_cobertura(
        df_documentos
    )

    salvar_resultados(
        df_documentos,
        df_cobertura,
    )

    print(f"\nDocumentos extraídos: {len(df_documentos):,}")

    print("\nCobertura por tipo de entidade:")
    print(df_cobertura.to_string(index=False))

    print("\nPrincipais tipos de documento:")
    print(
        df_documentos["tipo_documento"]
        .value_counts()
        .head(15)
        .to_string()
    )

    print("\nDocumentos sem número:")
    print(
        int(
            df_documentos["numero_documento"]
            .eq("")
            .sum()
        )
    )
