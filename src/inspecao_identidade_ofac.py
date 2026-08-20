from pathlib import Path
from xml.etree import ElementTree as ET

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")

DETAIL_TYPES = {"1432", "1433"}
LOCATIONS = {"186082"}


def nome_local(tag: str) -> str:
    """Remove o namespace XML."""
    return tag.rsplit("}", 1)[-1]


def texto_limpo(texto: str | None) -> str:
    """Remove espaços excedentes."""
    if not texto:
        return ""

    return " ".join(texto.split())


def imprimir_subarvore(
    elemento: ET.Element,
    titulo: str,
) -> None:
    """Exibe os valores relevantes de uma pequena subárvore."""
    print(f"\n=== {titulo} ===")

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


def inspecionar(caminho: Path) -> None:
    """Localiza referências específicas de identidade."""
    encontrados_detail = set()
    encontrados_location = set()

    capturando = None
    profundidade = 0

    contexto = ET.iterparse(
        caminho,
        events=("start", "end"),
    )

    for evento, elemento in contexto:
        tag = nome_local(elemento.tag)

        if evento == "start":
            if capturando is None:
                elemento_id = elemento.attrib.get("ID", "")

                if (
                    tag == "DetailType"
                    and elemento_id in DETAIL_TYPES
                ):
                    capturando = ("DetailType", elemento_id)
                    profundidade = 1

                elif (
                    tag == "Location"
                    and elemento_id in LOCATIONS
                ):
                    capturando = ("Location", elemento_id)
                    profundidade = 1

            else:
                profundidade += 1

        elif evento == "end":
            if capturando is not None:
                tag_alvo, id_alvo = capturando

                if tag == tag_alvo and profundidade == 1:
                    imprimir_subarvore(
                        elemento,
                        f"{tag_alvo} ID={id_alvo}",
                    )

                    if tag_alvo == "DetailType":
                        encontrados_detail.add(id_alvo)
                    else:
                        encontrados_location.add(id_alvo)

                    elemento.clear()
                    capturando = None
                    profundidade = 0

                else:
                    profundidade -= 1

            else:
                elemento.clear()

        if (
            encontrados_detail == DETAIL_TYPES
            and encontrados_location == LOCATIONS
        ):
            break


if __name__ == "__main__":
    inspecionar(ARQUIVO_OFAC)
