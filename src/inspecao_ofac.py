from pathlib import Path
from xml.etree import ElementTree as ET

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")


def nome_local(tag: str) -> str:
    """Remove o namespace XML e mantém apenas o nome da tag."""
    return tag.rsplit("}", 1)[-1]


def inspecionar_primeira_entidade(caminho: Path) -> None:
    """Localiza a primeira DistinctParty e exibe sua estrutura."""
    dentro_entidade = False
    profundidade_entidade = 0
    caminhos = []
    caminho_atual = []

    contexto = ET.iterparse(
        caminho,
        events=("start", "end"),
    )

    for evento, elemento in contexto:
        tag = nome_local(elemento.tag)

        if evento == "start":
            if tag == "DistinctParty" and not dentro_entidade:
                dentro_entidade = True
                profundidade_entidade = 1
                caminho_atual = [tag]
                caminhos.append(tag)
                continue

            if dentro_entidade:
                profundidade_entidade += 1
                caminho_atual.append(tag)

                caminho = " > ".join(caminho_atual)

                if caminho not in caminhos:
                    caminhos.append(caminho)

        elif evento == "end" and dentro_entidade:
            if tag == "DistinctParty" and profundidade_entidade == 1:
                break

            if caminho_atual:
                caminho_atual.pop()

            profundidade_entidade -= 1
            elemento.clear()

    print("Estrutura da primeira DistinctParty:\n")

    for caminho in caminhos:
        print(f"- {caminho}")


if __name__ == "__main__":
    inspecionar_primeira_entidade(ARQUIVO_OFAC)
