from pathlib import Path
from xml.etree import ElementTree as ET

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")

FEATURES_INTERESSE = {
    "8": "Birthdate",
    "9": "Place of Birth",
    "10": "Nationality Country",
    "11": "Citizenship Country",
    "25": "Location",
    "224": "Gender",
}

LIMITE_POR_FEATURE = 2


def nome_local(tag: str) -> str:
    """Remove o namespace XML."""
    return tag.rsplit("}", 1)[-1]


def texto_limpo(texto: str | None) -> str:
    """Remove espaços excedentes."""
    if not texto:
        return ""

    return " ".join(texto.split())


def imprimir_feature(
    elemento: ET.Element,
    feature_id: str,
) -> None:
    """Exibe a estrutura e os valores de uma feature."""
    print(
        f"\n=== {FEATURES_INTERESSE[feature_id]} "
        f"(FeatureTypeID={feature_id}) ==="
    )

    for item in elemento.iter():
        tag = nome_local(item.tag)
        texto = texto_limpo(item.text)

        atributos = {
            nome_local(chave): valor
            for chave, valor in item.attrib.items()
        }

        if texto or atributos:
            print(
                {
                    "tag": tag,
                    "atributos": atributos,
                    "valor": texto,
                }
            )


def inspecionar_features(caminho: Path) -> None:
    """Localiza exemplos das features relevantes sem carregar todo o XML."""
    contagens = {
        feature_id: 0
        for feature_id in FEATURES_INTERESSE
    }

    capturando = None
    profundidade = 0

    contexto = ET.iterparse(
        caminho,
        events=("start", "end"),
    )

    for evento, elemento in contexto:
        tag = nome_local(elemento.tag)

        if evento == "start":
            if (
                tag == "Feature"
                and capturando is None
            ):
                feature_id = elemento.attrib.get(
                    "FeatureTypeID",
                    "",
                )

                if (
                    feature_id in FEATURES_INTERESSE
                    and contagens[feature_id]
                    < LIMITE_POR_FEATURE
                ):
                    capturando = feature_id
                    profundidade = 1

            elif capturando is not None:
                profundidade += 1

        elif evento == "end":
            if capturando is not None:
                if tag == "Feature" and profundidade == 1:
                    imprimir_feature(
                        elemento,
                        capturando,
                    )

                    contagens[capturando] += 1

                    elemento.clear()
                    capturando = None
                    profundidade = 0
                else:
                    profundidade -= 1

            else:
                elemento.clear()

        if all(
            quantidade >= LIMITE_POR_FEATURE
            for quantidade in contagens.values()
        ):
            break


if __name__ == "__main__":
    inspecionar_features(ARQUIVO_OFAC)
