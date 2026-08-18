from pathlib import Path
from xml.etree import ElementTree as ET

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")
LIMITE_LINHAS = 100


def nome_local(tag: str) -> str:
    """Remove o namespace XML."""
    return tag.rsplit("}", 1)[-1]


def texto_limpo(texto: str | None) -> str:
    """Remove espaços excedentes do conteúdo textual."""
    if not texto:
        return ""

    return " ".join(texto.split())


def exibir_subarvore(elemento: ET.Element) -> None:
    """Exibe atributos e valores da primeira entidade encontrada."""
    linhas_exibidas = 0

    for item in elemento.iter():
        if linhas_exibidas >= LIMITE_LINHAS:
            break

        tag = nome_local(item.tag)
        texto = texto_limpo(item.text)

        atributos = {
            nome_local(chave): valor
            for chave, valor in item.attrib.items()
        }

        if not texto and not atributos:
            continue

        print(f"\nTag: {tag}")

        if atributos:
            print(f"Atributos: {atributos}")

        if texto:
            print(f"Valor: {texto[:300]}")

        linhas_exibidas += 1


def inspecionar_primeira_entidade(caminho: Path) -> None:
    """Localiza e exibe a primeira DistinctParty sem carregar todo o XML."""
    dentro_entidade = False

    contexto = ET.iterparse(
        caminho,
        events=("start", "end"),
    )

    for evento, elemento in contexto:
        tag = nome_local(elemento.tag)

        if evento == "start" and tag == "DistinctParty":
            dentro_entidade = True

        elif evento == "end" and tag == "DistinctParty" and dentro_entidade:
            exibir_subarvore(elemento)
            elemento.clear()
            break

        elif evento == "end" and not dentro_entidade:
            elemento.clear()


if __name__ == "__main__":
    inspecionar_primeira_entidade(ARQUIVO_OFAC)
