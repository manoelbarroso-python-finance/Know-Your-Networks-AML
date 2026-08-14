import re
import unicodedata


def normalizar_texto(valor: str | None) -> str:
    """Padroniza texto para comparação preservando o valor original fora desta função."""
    if valor is None:
        return ""

    texto = unicodedata.normalize("NFKD", valor)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = texto.casefold()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def normalizar_nome(nome: str | None) -> str:
    """Normaliza nomes sem remover partículas como de, da ou dos."""
    return normalizar_texto(nome)
