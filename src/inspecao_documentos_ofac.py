from pathlib import Path
from xml.etree import ElementTree as ET

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")

LIMITE_DOCUMENTOS = 3


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
    numero: int,
) -> None:
    """Exibe a estrutura de um documento de identificação."""
    print(f"\n=== Documento {numero} ===")

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


def inspecionar_documentos(caminho: Path) -> None:
    """Localiza os primeiros documentos de identificação."""
    quantidade = 0

    contexto = ET.iterparse(
        caminho,
        events=("end",),
    )

    for _, elemento in contexto:
        tag = nome_local(elemento.tag)

        if tag != "IDRegDocument":
            continue

        quantidade += 1

        imprimir_subarvore(
            elemento,
            quantidade,
        )

        elemento.clear()

        if quantidade >= LIMITE_DOCUMENTOS:
            break


if __name__ == "__main__":
    inspecionar_documentos(ARQUIVO_OFAC)
