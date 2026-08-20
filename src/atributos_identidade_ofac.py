from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")

ARQUIVO_ATRIBUTOS = Path(
    "data/processed/private/ofac_atributos_identidade.csv"
)

ARQUIVO_COBERTURA = Path(
    "data/processed/public/ofac_cobertura_identidade.csv"
)

FEATURES = {
    "8": "data_nascimento",
    "9": "local_nascimento",
    "10": "nacionalidade",
    "11": "cidadania",
    "224": "genero",
}


def nome_local(tag: str) -> str:
    """Remove o namespace XML."""
    return tag.rsplit("}", 1)[-1]


def texto_limpo(texto: str | None) -> str:
    """Remove espaços excedentes."""
    if not texto:
        return ""

    return " ".join(texto.split())


def valores_unicos(valores: list[str]) -> str:
    """Combina valores distintos preservando a ordem."""
    return " | ".join(dict.fromkeys(valor for valor in valores if valor))


def extrair_textos(elemento: ET.Element) -> list[str]:
    """Extrai valores textuais úteis de uma subárvore XML."""
    valores = []

    for item in elemento.iter():
        texto = texto_limpo(item.text)

        if texto:
            valores.append(texto)

    return valores


def extrair_data(
    elemento: ET.Element,
) -> tuple[str, str, bool]:
    """Extrai data preservando precisão e indicação de aproximação."""
    valores = {
        "Year": "",
        "Month": "",
        "Day": "",
    }

    aproximada = False

    for item in elemento.iter():
        tag = nome_local(item.tag)

        if tag == "Start":
            aproximada = (
                item.attrib.get("Approximate", "false").lower()
                == "true"
            )

        if tag in valores and not valores[tag]:
            valores[tag] = texto_limpo(item.text)

    ano = valores["Year"]
    mes = valores["Month"]
    dia = valores["Day"]

    if ano and mes and dia:
        return (
            f"{int(ano):04d}-{int(mes):02d}-{int(dia):02d}",
            "dia",
            aproximada,
        )

    if ano and mes:
        return (
            f"{int(ano):04d}-{int(mes):02d}",
            "mes",
            aproximada,
        )

    if ano:
        return ano, "ano", aproximada

    return "", "ausente", aproximada


def construir_mapa_localizacoes(
    caminho: Path,
) -> dict[str, str]:
    """Cria mapa LocationID → descrição textual."""
    mapa = {}

    contexto = ET.iterparse(
        caminho,
        events=("end",),
    )

    for _, elemento in contexto:
        if nome_local(elemento.tag) != "Location":
            continue

        location_id = elemento.attrib.get("ID", "")

        valores = [
            texto
            for texto in extrair_textos(elemento)
            if texto
        ]

        if location_id:
            mapa[location_id] = valores_unicos(valores)

        elemento.clear()

    return mapa


def extrair_valor_feature(
    feature: ET.Element,
    feature_id: str,
    localizacoes: dict[str, str],
) -> tuple[str, str, bool]:
    """Extrai o valor de uma feature de identidade."""
    if feature_id == "8":
        return extrair_data(feature)

    locations = [
        item.attrib.get("LocationID", "")
        for item in feature.iter()
        if nome_local(item.tag) == "VersionLocation"
    ]

    valores_localizacao = [
        localizacoes.get(location_id, "")
        for location_id in locations
        if location_id
    ]

    if valores_localizacao:
        return valores_unicos(valores_localizacao), "", False

    textos = extrair_textos(feature)

    return valores_unicos(textos), "", False


def extrair_atributos(
    caminho: Path,
    localizacoes: dict[str, str],
) -> pd.DataFrame:
    """Extrai atributos relevantes por entidade OFAC."""
    registros = []

    contexto = ET.iterparse(
        caminho,
        events=("end",),
    )

    for _, elemento in contexto:
        if nome_local(elemento.tag) != "DistinctParty":
            continue

        ofac_id = elemento.attrib.get("FixedRef", "")

        registro = {
            "ofac_id": ofac_id,
            "data_nascimento": "",
            "precisao_nascimento": "",
            "nascimento_aproximado": False,
            "local_nascimento": "",
            "nacionalidade": "",
            "cidadania": "",
            "genero": "",
        }

        acumulados = {
            "local_nascimento": [],
            "nacionalidade": [],
            "cidadania": [],
            "genero": [],
        }

        for feature in elemento.iter():
            if nome_local(feature.tag) != "Feature":
                continue

            feature_id = feature.attrib.get("FeatureTypeID", "")

            if feature_id not in FEATURES:
                continue

            campo = FEATURES[feature_id]

            valor, precisao, aproximada = extrair_valor_feature(
                feature,
                feature_id,
                localizacoes,
            )

            if campo == "data_nascimento":
                if valor and not registro["data_nascimento"]:
                    registro["data_nascimento"] = valor
                    registro["precisao_nascimento"] = precisao
                    registro["nascimento_aproximado"] = aproximada
            elif valor:
                acumulados[campo].append(valor)

        for campo, valores in acumulados.items():
            registro[campo] = valores_unicos(valores)

        registros.append(registro)

        elemento.clear()

    return pd.DataFrame(registros)


def calcular_cobertura(
    atributos: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula cobertura dos atributos de identidade."""
    campos = [
        "data_nascimento",
        "local_nascimento",
        "nacionalidade",
        "cidadania",
        "genero",
    ]

    total = len(atributos)
    registros = []

    for campo in campos:
        quantidade = atributos[campo].ne("").sum()

        registros.append(
            {
                "atributo": campo,
                "entidades_com_informacao": int(quantidade),
                "total_entidades": total,
                "cobertura_pct": round(
                    quantidade / total * 100,
                    2,
                ),
            }
        )

    return pd.DataFrame(registros)


def salvar_resultados(
    atributos: pd.DataFrame,
    cobertura: pd.DataFrame,
) -> None:
    """Salva dados privados e estatísticas públicas."""
    ARQUIVO_ATRIBUTOS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARQUIVO_COBERTURA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    atributos.to_csv(
        ARQUIVO_ATRIBUTOS,
        index=False,
        encoding="utf-8",
    )

    cobertura.to_csv(
        ARQUIVO_COBERTURA,
        index=False,
        encoding="utf-8",
    )


if __name__ == "__main__":
    print("Construindo mapa de localizações...")

    mapa_localizacoes = construir_mapa_localizacoes(
        ARQUIVO_OFAC
    )

    print(
        f"Localizações identificadas: "
        f"{len(mapa_localizacoes):,}"
    )

    print("Extraindo atributos de identidade...")

    df_atributos = extrair_atributos(
        ARQUIVO_OFAC,
        mapa_localizacoes,
    )

    df_cobertura = calcular_cobertura(
        df_atributos
    )

    salvar_resultados(
        df_atributos,
        df_cobertura,
    )

    print("\nCobertura dos atributos:")
    print(df_cobertura.to_string(index=False))

    print(
        "\nAtributos privados salvos em: "
        "data/processed/private/"
    )
