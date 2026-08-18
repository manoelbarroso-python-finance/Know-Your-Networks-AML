import re
import unicodedata
from datetime import date, datetime


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
def normalizar_data(
    valor: str | date | datetime | None,
) -> tuple[str, str]:
    """Padroniza datas preservando o nível de precisão informado."""
    if valor is None:
        return "", "ausente"

    if isinstance(valor, datetime):
        return valor.date().isoformat(), "dia"

    if isinstance(valor, date):
        return valor.isoformat(), "dia"

    texto = valor.strip()

    if not texto:
        return "", "ausente"

    # YYYY-MM-DD
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        try:
            return date.fromisoformat(texto).isoformat(), "dia"
        except ValueError:
            return "", "invalida"

    # DD/MM/YYYY ou DD-MM-YYYY
    match_data = re.fullmatch(
        r"(\d{2})[/-](\d{2})[/-](\d{4})",
        texto,
    )

    if match_data:
        dia, mes, ano = map(int, match_data.groups())

        try:
            data_normalizada = date(ano, mes, dia)
            return data_normalizada.isoformat(), "dia"
        except ValueError:
            return "", "invalida"

    # YYYY-MM
    match_mes = re.fullmatch(r"(\d{4})-(\d{2})", texto)

    if match_mes:
        ano, mes = map(int, match_mes.groups())

        try:
            date(ano, mes, 1)
            return texto, "mes"
        except ValueError:
            return "", "invalida"

    # YYYY
    if re.fullmatch(r"\d{4}", texto):
        ano = int(texto)

        try:
            date(ano, 1, 1)
            return texto, "ano"
        except ValueError:
            return "", "invalida"

    return "", "invalida"
