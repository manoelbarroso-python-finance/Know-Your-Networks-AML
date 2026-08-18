from pathlib import Path

import requests

URL_OFAC_SDN = (
    "https://sanctionslistservice.ofac.treas.gov/"
    "api/download/sdn_advanced.xml"
)

PASTA_DESTINO = Path("data/raw/ofac")
ARQUIVO_DESTINO = PASTA_DESTINO / "sdn_advanced.xml"


def baixar_sdn_ofac() -> Path:
    """Baixa o SDN Advanced XML da OFAC e preserva o arquivo bruto."""
    PASTA_DESTINO.mkdir(parents=True, exist_ok=True)

    resposta = requests.get(
        URL_OFAC_SDN,
        timeout=120,
    )
    resposta.raise_for_status()

    ARQUIVO_DESTINO.write_bytes(resposta.content)

    return ARQUIVO_DESTINO


if __name__ == "__main__":
    arquivo = baixar_sdn_ofac()
    print(f"Arquivo salvo em: {arquivo}")
