from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

from src.conexao_neo4j import carregar_configuracao

ARQUIVO_RESULTADOS = Path(
    "data/processed/public/aml_padroes_detectados.csv"
)

ARQUIVO_GROUND_TRUTH = Path(
    "data/synthetic/ground_truth_transacoes.csv"
)


def detectar_fluxos_circulares(driver) -> pd.DataFrame:
    """Detecta ciclos A → B → C → A em janela temporal curta."""
    query = """
    MATCH
        (a:Account)-[t1:TRANSFERRED_TO]->(b:Account),
        (b)-[t2:TRANSFERRED_TO]->(c:Account),
        (c)-[t3:TRANSFERRED_TO]->(a)

    WHERE
        a <> b
        AND b <> c
        AND a <> c

        AND t1.timestamp < t2.timestamp
        AND t2.timestamp < t3.timestamp

        AND duration.between(
            t1.timestamp,
            t3.timestamp
        ).hours <= 6

        AND t1.valor >= 5000
        AND t2.valor >= 5000
        AND t3.valor >= 5000

        AND t2.valor >= t1.valor * 0.80
        AND t3.valor >= t2.valor * 0.80

    RETURN
        a.id AS conta_a,
        b.id AS conta_b,
        c.id AS conta_c,
        t1.tx_id AS tx_1,
        t2.tx_id AS tx_2,
        t3.tx_id AS tx_3,
        t1.valor AS valor_1,
        t2.valor AS valor_2,
        t3.valor AS valor_3,
        t1.timestamp AS inicio,
        t3.timestamp AS fim
    """

    registros, _, _ = driver.execute_query(
        query,
        database_="neo4j",
    )

    return pd.DataFrame(
        [dict(registro) for registro in registros]
    )


def carregar_movimentacoes(driver) -> pd.DataFrame:
    """Carrega transações do Neo4j para análise temporal em Python."""
    query = """
    MATCH
        (origem:Account)
        -[t:TRANSFERRED_TO]->
        (destino:Account)

    RETURN
        t.tx_id AS tx_id,
        origem.id AS origem,
        destino.id AS destino,
        t.valor AS valor,
        t.timestamp AS timestamp
    """

    registros, _, _ = driver.execute_query(
        query,
        database_="neo4j",
    )

    dados = pd.DataFrame(
        [dict(registro) for registro in registros]
    )

    dados["valor"] = pd.to_numeric(
        dados["valor"],
        errors="raise",
    )

    dados["timestamp"] = pd.to_datetime(
        dados["timestamp"].astype(str),
        errors="raise",
    )

    return dados.sort_values(
        "timestamp"
    ).reset_index(drop=True)


def detectar_concentracao_repasse(
    transacoes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detecta múltiplas entradas seguidas de repasse rápido.

    Critérios:
    - pelo menos 4 remetentes distintos;
    - entradas concentradas em até 2 horas;
    - soma das entradas >= USD 9.000;
    - saída em até 1 hora após a última entrada;
    - repasse >= 80% do valor concentrado.
    """
    resultados = []

    for conta in transacoes["destino"].unique():
        entradas = transacoes[
            transacoes["destino"] == conta
        ].copy()

        if len(entradas) < 4:
            continue

        entradas = entradas.sort_values(
            "timestamp"
        ).reset_index(drop=True)

        for inicio in range(len(entradas)):
            instante_inicial = entradas.loc[
                inicio,
                "timestamp",
            ]

            limite = (
                instante_inicial
                + pd.Timedelta(hours=2)
            )

            janela = entradas[
                (entradas["timestamp"] >= instante_inicial)
                & (entradas["timestamp"] <= limite)
            ]

            remetentes = (
                janela["origem"]
                .drop_duplicates()
            )

            if len(remetentes) < 4:
                continue

            valor_entradas = float(
                janela["valor"].sum()
            )

            if valor_entradas < 9000:
                continue

            ultima_entrada = janela[
                "timestamp"
            ].max()

            limite_saida = (
                ultima_entrada
                + pd.Timedelta(hours=1)
            )

            saidas = transacoes[
                (transacoes["origem"] == conta)
                & (
                    transacoes["timestamp"]
                    > ultima_entrada
                )
                & (
                    transacoes["timestamp"]
                    <= limite_saida
                )
            ].copy()

            if saidas.empty:
                continue

            saidas = saidas[
                saidas["valor"]
                >= valor_entradas * 0.80
            ]

            if saidas.empty:
                continue

            saida = (
                saidas.sort_values(
                    "timestamp"
                )
                .iloc[0]
            )

            resultados.append(
                {
                    "conta_central": conta,
                    "qtd_remetentes": len(
                        remetentes
                    ),
                    "valor_entradas": round(
                        valor_entradas,
                        2,
                    ),
                    "conta_destino": str(
                        saida["destino"]
                    ),
                    "valor_repasse": float(
                        saida["valor"]
                    ),
                    "inicio": instante_inicial,
                    "fim": saida["timestamp"],
                }
            )

            break

    return pd.DataFrame(
        resultados
    )


def avaliar_resultados(
    ciclos: pd.DataFrame,
    concentracoes: pd.DataFrame,
) -> pd.DataFrame:
    """Compara os padrões detectados ao ground truth conhecido."""
    esperado_ciclo = {
        "ACCOUNT_010",
        "ACCOUNT_011",
        "ACCOUNT_012",
    }

    ciclo_detectado = False

    if not ciclos.empty:
        for _, linha in ciclos.iterrows():
            contas = {
                linha["conta_a"],
                linha["conta_b"],
                linha["conta_c"],
            }

            if contas == esperado_ciclo:
                ciclo_detectado = True
                break

    concentracao_detectada = False

    if not concentracoes.empty:
        concentracao_detectada = bool(
            (
                concentracoes["conta_central"]
                == "ACCOUNT_005"
            ).any()
        )

    return pd.DataFrame(
        [
            {
                "pattern_id": "GT_TX_001",
                "tipo": "Fluxo circular",
                "detectado": ciclo_detectado,
                "candidatos": len(ciclos),
            },
            {
                "pattern_id": "GT_TX_002",
                "tipo": (
                    "Concentração e repasse rápido"
                ),
                "detectado": concentracao_detectada,
                "candidatos": len(
                    concentracoes
                ),
            },
        ]
    )


if __name__ == "__main__":
    uri, usuario, senha = (
        carregar_configuracao()
    )

    with GraphDatabase.driver(
        uri,
        auth=(
            usuario,
            senha,
        ),
    ) as driver:
        driver.verify_connectivity()

        df_ciclos = detectar_fluxos_circulares(
            driver
        )

        df_transacoes = carregar_movimentacoes(
            driver
        )

    df_concentracao = (
        detectar_concentracao_repasse(
            df_transacoes
        )
    )

    df_avaliacao = avaliar_resultados(
        df_ciclos,
        df_concentracao,
    )

    resultados = []

    if not df_ciclos.empty:
        for _, linha in df_ciclos.iterrows():
            resultados.append(
                {
                    "tipo": "Fluxo circular",
                    "conta_principal": linha[
                        "conta_a"
                    ],
                    "detalhe": (
                        f"{linha['conta_a']} > "
                        f"{linha['conta_b']} > "
                        f"{linha['conta_c']} > "
                        f"{linha['conta_a']}"
                    ),
                }
            )

    if not df_concentracao.empty:
        for _, linha in (
            df_concentracao.iterrows()
        ):
            resultados.append(
                {
                    "tipo": (
                        "Concentração e repasse rápido"
                    ),
                    "conta_principal": linha[
                        "conta_central"
                    ],
                    "detalhe": (
                        f"{linha['qtd_remetentes']} "
                        "remetentes > "
                        f"{linha['conta_central']} > "
                        f"{linha['conta_destino']}"
                    ),
                }
            )

    df_resultados = pd.DataFrame(
        resultados
    )

    ARQUIVO_RESULTADOS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_resultados.to_csv(
        ARQUIVO_RESULTADOS,
        index=False,
        encoding="utf-8",
    )

    print("\nAvaliação dos padrões AML:")
    print(
        df_avaliacao.to_string(
            index=False
        )
    )

    print("\nFluxos circulares detectados:")

    if df_ciclos.empty:
        print("Nenhum.")
    else:
        print(
            df_ciclos[
                [
                    "conta_a",
                    "conta_b",
                    "conta_c",
                    "valor_1",
                    "valor_2",
                    "valor_3",
                ]
            ].to_string(
                index=False
            )
        )

    print(
        "\nConcentração + repasse detectados:"
    )

    if df_concentracao.empty:
        print("Nenhum.")
    else:
        print(
            df_concentracao[
                [
                    "conta_central",
                    "qtd_remetentes",
                    "valor_entradas",
                    "conta_destino",
                    "valor_repasse",
                ]
            ].to_string(
                index=False
            )
        )
