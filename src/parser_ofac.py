from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

from src.normalizacao import normalizar_nome

ARQUIVO_OFAC = Path("data/raw/ofac/sdn_advanced.xml")
PASTA_SAIDA = Path("data/processed/private")

ARQUIVO_ENTIDADES = PASTA_SAIDA / "ofac_entidades.csv"
ARQUIVO_ALIASES = PASTA_SAIDA / "ofac_aliases.csv"


def nome_local(tag: str) -> str:
    """Remove o namespace XML."""
    return tag.rsplit("}", 1)[-1]


def texto_limpo(texto: str | None) -> str:
    """Remove espaços excedentes."""
    if not texto:
        return ""

    return " ".join(texto.split())


def valor_booleano(valor: str | None) -> bool:
    """Converte booleanos textuais do XML."""
    return valor == "true"


def obter_identidade_principal(
    entidade: ET.Element,
) -> ET.Element | None:
    """Retorna a identidade marcada como principal."""
    identidades = [
        elemento
        for elemento in entidade.iter()
        if nome_local(elemento.tag) == "Identity"
    ]

    for identidade in identidades:
        if valor_booleano(identidade.attrib.get("Primary")):
            return identidade

    return identidades[0] if identidades else None


def extrair_nomes_documentados(
    alias: ET.Element,
) -> list[tuple[str, str, str]]:
    """Extrai nomes documentados e seus respectivos scripts."""
    nomes = []

    for elemento in alias:
        if nome_local(elemento.tag) != "DocumentedName":
            continue

        partes = []
        scripts = []

        for item in elemento.iter():
            if nome_local(item.tag) != "NamePartValue":
                continue

            texto = texto_limpo(item.text)

            if texto:
                partes.append(texto)

            script_id = item.attrib.get("ScriptID", "")

            if script_id:
                scripts.append(script_id)

        if partes:
            nomes.append(
                (
                    elemento.attrib.get("ID", ""),
                    " ".join(partes),
                    "|".join(sorted(set(scripts))),
                )
            )

    return nomes


def extrair_entidade(
    elemento: ET.Element,
) -> tuple[dict | None, list[dict]]:
    """Extrai uma entidade OFAC e suas representações nominais."""
    ofac_id = elemento.attrib.get("FixedRef", "")

    profile = next(
        (
            item
            for item in elemento
            if nome_local(item.tag) == "Profile"
        ),
        None,
    )

    identidade = obter_identidade_principal(elemento)

    if profile is None or identidade is None:
        return None, []

    aliases = []
    nome_principal = ""

    for alias in identidade:
        if nome_local(alias.tag) != "Alias":
            continue

        primary = valor_booleano(alias.attrib.get("Primary"))
        low_quality = valor_booleano(alias.attrib.get("LowQuality"))

        nomes_documentados = extrair_nomes_documentados(alias)

        for documented_name_id, nome, script_id in nomes_documentados:
            if primary and not nome_principal:
                nome_principal = nome

            aliases.append(
                {
                    "ofac_id": ofac_id,
                    "identity_id": identidade.attrib.get("ID", ""),
                    "documented_name_id": documented_name_id,
                    "alias_type_id": alias.attrib.get("AliasTypeID", ""),
                    "script_id": script_id,
                    "primary": primary,
                    "low_quality": low_quality,
                    "nome_original": nome,
                    "nome_normalizado": normalizar_nome(nome),
                }
            )

    entidade = {
        "ofac_id": ofac_id,
        "party_subtype_id": profile.attrib.get("PartySubTypeID", ""),
        "identity_id": identidade.attrib.get("ID", ""),
        "nome_principal": nome_principal,
        "nome_principal_normalizado": normalizar_nome(nome_principal),
    }

    return entidade, aliases


def processar_ofac() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Processa entidades e aliases da SDN List."""
    entidades = []
    aliases = []
    dentro_entidade = False

    contexto = ET.iterparse(
        ARQUIVO_OFAC,
        events=("start", "end"),
    )

    for evento, elemento in contexto:
        tag = nome_local(elemento.tag)

        if evento == "start" and tag == "DistinctParty":
            dentro_entidade = True

        elif evento == "end" and tag == "DistinctParty":
            entidade, aliases_entidade = extrair_entidade(elemento)

            if entidade:
                entidades.append(entidade)
                aliases.extend(aliases_entidade)

            elemento.clear()
            dentro_entidade = False

        elif evento == "end" and not dentro_entidade:
            elemento.clear()

    df_entidades = pd.DataFrame(entidades)
    df_aliases = pd.DataFrame(aliases)

    return df_entidades, df_aliases


def validar_resultados(
    entidades: pd.DataFrame,
    aliases: pd.DataFrame,
) -> None:
    """Impede que resultados claramente inválidos sejam salvos."""
    if entidades.empty:
        raise ValueError("Nenhuma entidade OFAC foi extraída.")

    if aliases.empty:
        raise ValueError(
            "Nenhum alias OFAC foi extraído. "
            "O parser deve ser revisado antes de salvar."
        )

    if "script_id" not in aliases.columns:
        raise ValueError("A coluna script_id não foi criada.")


def salvar_resultados(
    entidades: pd.DataFrame,
    aliases: pd.DataFrame,
) -> None:
    """Salva os datasets processados."""
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    entidades.to_csv(
        ARQUIVO_ENTIDADES,
        index=False,
        encoding="utf-8",
    )

    aliases.to_csv(
        ARQUIVO_ALIASES,
        index=False,
        encoding="utf-8",
    )


if __name__ == "__main__":
    df_entidades, df_aliases = processar_ofac()

    validar_resultados(
        df_entidades,
        df_aliases,
    )

    salvar_resultados(
        df_entidades,
        df_aliases,
    )

    print(f"Entidades: {len(df_entidades):,}")
    print(f"Aliases: {len(df_aliases):,}")
    print(f"Entidades salvas em: {ARQUIVO_ENTIDADES}")
    print(f"Aliases salvos em: {ARQUIVO_ALIASES}")
