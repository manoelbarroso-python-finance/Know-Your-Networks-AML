from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

ARQUIVO_BENCHMARK = Path(
    "data/processed/private/ofac_benchmark_individuos.csv"
)

ARQUIVO_FEATURES = Path(
    "data/processed/private/ofac_matching_features.csv"
)


def texto_disponivel(valor: str) -> bool:
    """Indica se um atributo está disponível."""
    return bool(valor.strip())


def comparar_texto(
    valor_a: str,
    valor_b: str,
) -> tuple[int, int]:
    """Retorna disponibilidade conjunta e correspondência exata."""
    observado = int(
        texto_disponivel(valor_a)
        and texto_disponivel(valor_b)
    )

    if not observado:
        return 0, 0

    match = int(
        valor_a.strip().casefold()
        == valor_b.strip().casefold()
    )

    return observado, match


def documentos_para_set(valor: str) -> set[str]:
    """Transforma documentos concatenados em conjunto."""
    if not texto_disponivel(valor):
        return set()

    return {
        documento.strip()
        for documento in valor.split("|")
        if documento.strip()
    }


def comparar_documentos(
    valor_a: str,
    valor_b: str,
) -> tuple[int, int]:
    """Avalia se existem documentos comparáveis e coincidentes."""
    docs_a = documentos_para_set(valor_a)
    docs_b = documentos_para_set(valor_b)

    observado = int(bool(docs_a) and bool(docs_b))

    if not observado:
        return 0, 0

    match = int(bool(docs_a.intersection(docs_b)))

    return observado, match


def criar_features(
    benchmark: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói evidências utilizadas pelos modelos de matching."""
    registros = []

    for _, linha in benchmark.iterrows():
        nascimento_obs, nascimento_match = comparar_texto(
            linha["data_nascimento_origem"],
            linha["data_nascimento_candidato"],
        )

        local_obs, local_match = comparar_texto(
            linha["local_nascimento_origem"],
            linha["local_nascimento_candidato"],
        )

        nacionalidade_obs, nacionalidade_match = comparar_texto(
            linha["nacionalidade_origem"],
            linha["nacionalidade_candidato"],
        )

        cidadania_obs, cidadania_match = comparar_texto(
            linha["cidadania_origem"],
            linha["cidadania_candidato"],
        )

        documento_obs, documento_match = comparar_documentos(
            linha["documentos_origem"],
            linha["documentos_candidato"],
        )

        nome_score = fuzz.WRatio(
            linha["nome_consulta_normalizado"],
            linha["nome_candidato_normalizado"],
        ) / 100

        registros.append(
            {
                "ofac_id_origem": linha["ofac_id_origem"],
                "ofac_id_candidato": linha["ofac_id_candidato"],
                "match_real": linha["match_real"],
                "nome_score": round(nome_score, 4),
                "nascimento_observado": nascimento_obs,
                "nascimento_match": nascimento_match,
                "local_observado": local_obs,
                "local_match": local_match,
                "nacionalidade_observada": nacionalidade_obs,
                "nacionalidade_match": nacionalidade_match,
                "cidadania_observada": cidadania_obs,
                "cidadania_match": cidadania_match,
                "documento_observado": documento_obs,
                "documento_match": documento_match,
                "low_quality": linha["low_quality"],
                "script": linha["script"],
            }
        )

    return pd.DataFrame(registros)


if __name__ == "__main__":
    df_benchmark = pd.read_csv(
        ARQUIVO_BENCHMARK,
        dtype=str,
    ).fillna("")

    df_features = criar_features(df_benchmark)

    df_features.to_csv(
        ARQUIVO_FEATURES,
        index=False,
        encoding="utf-8",
    )

    print(f"\nPares processados: {len(df_features):,}")

    print("\nMédia das evidências por classe:")

    colunas = [
        "nome_score",
        "nascimento_match",
        "local_match",
        "nacionalidade_match",
        "cidadania_match",
        "documento_match",
    ]

    print(
        df_features.groupby("match_real")[colunas]
        .mean()
        .round(3)
        .to_string()
    )

    print(f"\nArquivo salvo em: {ARQUIVO_FEATURES}")
