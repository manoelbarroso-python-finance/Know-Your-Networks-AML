from pathlib import Path
from xml.etree import ElementTree as ET

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")

GRUPOS_INTERESSE = {
    "PartyTypeValues",
    "PartySubTypeValues",
    "AliasTypeValues",
    "FeatureTypeValues",
    "NamePartTypeValues",
    "ScriptValues",
    "SanctionsProgramValues",
}

LIMITE_POR_GRUPO = 5


def nome_local(tag: str) -> str:
    """Remove o namespace XML."""
    return tag.rsplit("}", 1)[-1]


def texto_limpo(texto: str | None) -> str:
    """Remove espaços excedentes."""
    if not texto:
        return ""

    return " ".join(texto.split())


def exibir_referencias(caminho: Path) -> None:
    """Exibe uma pequena amostra das principais tabelas de referência."""
    grupo_atual = None
    contagens = {grupo: 0 for grupo in GRUPOS_INTERESSE}

    contexto = ET.iterparse(
        caminho,
        events=("start", "end"),
    )

    for evento, elemento in contexto:
        tag = nome_local(elemento.tag)

        if evento == "start" and tag in GRUPOS_INTERESSE:
            grupo_atual = tag
            print(f"\n=== {grupo_atual} ===")

        elif evento == "end" and grupo_atual:
            if tag == grupo_atual:
                grupo_atual = None
                elemento.clear()
                continue

            if contagens[grupo_atual] >= LIMITE_POR_GRUPO:
                elemento.clear()
                continue

            texto = texto_limpo(elemento.text)
            atributos = {
                nome_local(chave): valor
                for chave, valor in elemento.attrib.items()
            }

            if texto or atributos:
                print(
                    {
                        "tag": tag,
                        "atributos": atributos,
                        "valor": texto,
                    }
                )
                contagens[grupo_atual] += 1

            elemento.clear()


if __name__ == "__main__":
    exibir_referencias(ARQUIVO_OFAC)
