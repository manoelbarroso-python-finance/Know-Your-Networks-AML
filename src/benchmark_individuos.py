import re
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

ARQUIVO_POSITIVOS = Path(
    "data/processed/private/ofac_benchmark_matching.csv"
)

ARQUIVO_ENTIDADES = Path(
    "data/processed/private/ofac_entidades_enriquecidas.csv"
)

ARQUIVO_ATRIBUTOS = Path(
    "data/processed/private/ofac_atributos_identidade.csv"
)

ARQUIVO_DOCUMENTOS = Path(
    "data/processed/private/ofac_documentos.csv"
)

ARQUIVO_SAIDA = Path(
    "data/processed/private/ofac_benchmark_individuos.csv"
)


def normalizar_documento(valor: str) -> str:
    """Padroniza documentos para comparação."""
    return re.sub(
        r"[^A-Z0-9]",
        "",
        valor.upper(),
    )


def carregar_dados() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Carrega as bases necessárias ao benchmark."""
    positivos = pd.read_csv(
        ARQUIVO_POSITIVOS,
        dtype=str,
    ).fillna("")

    entidades = pd.read_csv(
        ARQUIVO_ENTIDADES,
        dtype=str,
    ).fillna("")

    atributos = pd.read_csv(
        ARQUIVO_ATRIBUTOS,
        dtype=str,
    ).fillna("")

    documentos = pd.read_csv(
        ARQUIVO_DOCUMENTOS,
        dtype=str,
    ).fillna("")

    return positivos, entidades, atributos, documentos


def preparar_documentos(
    documentos: pd.DataFrame,
) -> dict[str, str]:
    """Agrupa identificadores documentais por entidade."""
    dados = documentos[
        documentos["tipo_entidade"] == "Individual"
    ].copy()

    dados["documento_chave"] = (
        dados["tipo_documento"]
        + ":"
        + dados["numero_documento"].apply(
            normalizar_documento
        )
    )

    agrupados = (
        dados.groupby("ofac_id")["documento_chave"]
        .agg(
            lambda valores: " | ".join(
                sorted(set(valores))
            )
        )
    )

    return {
    str(ofac_id): str(valor)
    for ofac_id, valor in agrupados.items()
}


def preparar_atributos(
    atributos: pd.DataFrame,
) -> dict[str, dict[str, str]]:
    """Cria mapa de atributos de identidade por OFAC ID."""
    dados = atributos.set_index("ofac_id")

    return {
        str(ofac_id): {
            str(coluna): str(valor)
            for coluna, valor in linha.items()
        }
        for ofac_id, linha in dados.iterrows()
    }


def encontrar_hard_negative(
    nome_consulta: str,
    ofac_id_origem: str,
    nomes_candidatos: list[str],
    ids_candidatos: list[str],
) -> tuple[int, float]:
    """Encontra candidato nominalmente próximo com OFAC ID diferente."""
    resultados = process.extract(
        nome_consulta,
        nomes_candidatos,
        scorer=fuzz.WRatio,
        limit=10,
    )

    for _, score, indice in resultados:
        if ids_candidatos[indice] != ofac_id_origem:
            return indice, float(score)

    raise ValueError(
        f"Hard negative não encontrado para OFAC ID "
        f"{ofac_id_origem}."
    )


def adicionar_atributos(
    registro: dict,
    origem_id: str,
    candidato_id: str,
    atributos: dict[str, dict[str, str]],
    documentos: dict[str, str],
) -> dict:
    """Acrescenta evidências de identidade dos dois registros."""
    origem = atributos.get(origem_id, {})
    candidato = atributos.get(candidato_id, {})

    campos = [
        "data_nascimento",
        "local_nascimento",
        "nacionalidade",
        "cidadania",
    ]

    for campo in campos:
        registro[f"{campo}_origem"] = origem.get(
            campo,
            "",
        )

        registro[f"{campo}_candidato"] = candidato.get(
            campo,
            "",
        )

    registro["documentos_origem"] = documentos.get(
        origem_id,
        "",
    )

    registro["documentos_candidato"] = documentos.get(
        candidato_id,
        "",
    )

    return registro


def construir_benchmark(
    positivos: pd.DataFrame,
    entidades: pd.DataFrame,
    atributos: pd.DataFrame,
    documentos: pd.DataFrame,
) -> pd.DataFrame:
    """Cria pares positivos e hard negatives para indivíduos."""
    positivos = positivos[
        positivos["tipo_entidade"] == "Individual"
    ].copy()

    individuos = entidades[
        entidades["tipo_entidade"] == "Individual"
    ].copy()

    nomes_candidatos = individuos[
        "nome_principal_normalizado"
    ].tolist()

    ids_candidatos = individuos["ofac_id"].tolist()

    atributos_map = preparar_atributos(
        atributos
    )

    documentos_map = preparar_documentos(
        documentos
    )

    registros = []

    total = len(positivos)

    for numero, (_, linha) in enumerate(
        positivos.iterrows(),
        start=1,
    ):
        origem_id = linha["ofac_id"]

        positivo = {
            "ofac_id_origem": origem_id,
            "ofac_id_candidato": origem_id,
            "nome_consulta": linha["nome_b"],
            "nome_consulta_normalizado": linha[
                "nome_b_normalizado"
            ],
            "nome_candidato": linha["nome_a"],
            "nome_candidato_normalizado": linha[
                "nome_a_normalizado"
            ],
            "tipo_alias": linha["tipo_alias"],
            "low_quality": linha["low_quality"],
            "script": linha["script"],
            "match_real": True,
            "hard_negative_score": "",
        }

        registros.append(
            adicionar_atributos(
                positivo,
                origem_id,
                origem_id,
                atributos_map,
                documentos_map,
            )
        )

        indice, score = encontrar_hard_negative(
            linha["nome_b_normalizado"],
            origem_id,
            nomes_candidatos,
            ids_candidatos,
        )

        candidato = individuos.iloc[indice]
        candidato_id = candidato["ofac_id"]

        negativo = {
            "ofac_id_origem": origem_id,
            "ofac_id_candidato": candidato_id,
            "nome_consulta": linha["nome_b"],
            "nome_consulta_normalizado": linha[
                "nome_b_normalizado"
            ],
            "nome_candidato": candidato[
                "nome_principal"
            ],
            "nome_candidato_normalizado": candidato[
                "nome_principal_normalizado"
            ],
            "tipo_alias": linha["tipo_alias"],
            "low_quality": linha["low_quality"],
            "script": linha["script"],
            "match_real": False,
            "hard_negative_score": round(
                score,
                2,
            ),
        }

        registros.append(
            adicionar_atributos(
                negativo,
                origem_id,
                candidato_id,
                atributos_map,
                documentos_map,
            )
        )

        if numero % 2_000 == 0:
            print(
                f"Processados: {numero:,} / {total:,}"
            )

    return pd.DataFrame(registros)


def validar_benchmark(
    benchmark: pd.DataFrame,
) -> None:
    """Valida consistência básica do benchmark."""
    positivos = benchmark["match_real"].eq(True).sum()
    negativos = benchmark["match_real"].eq(False).sum()

    if positivos != negativos:
        raise ValueError(
            "Benchmark ficou desbalanceado."
        )

    negativos_invalidos = benchmark[
        benchmark["match_real"].eq(False)
        & (
            benchmark["ofac_id_origem"]
            == benchmark["ofac_id_candidato"]
        )
    ]

    if not negativos_invalidos.empty:
        raise ValueError(
            "Há hard negatives com o mesmo OFAC ID."
        )


if __name__ == "__main__":
    (
        df_positivos,
        df_entidades,
        df_atributos,
        df_documentos,
    ) = carregar_dados()

    benchmark = construir_benchmark(
        df_positivos,
        df_entidades,
        df_atributos,
        df_documentos,
    )

    validar_benchmark(benchmark)

    benchmark.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8",
    )

    print("\nBenchmark individual concluído.")

    print(f"Total de pares: {len(benchmark):,}")

    print(
        "Positivos: "
        f"{benchmark['match_real'].eq(True).sum():,}"
    )

    print(
        "Hard negatives: "
        f"{benchmark['match_real'].eq(False).sum():,}"
    )

    print(f"\nArquivo salvo em: {ARQUIVO_SAIDA}")
