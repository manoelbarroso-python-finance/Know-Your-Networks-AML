from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
)

from src.avaliacao_matching import (
    FEATURES,
    carregar_dados,
    escolher_threshold,
    separar_amostras,
)
from src.robustez_matching import (
    aplicar_divergencias,
    aplicar_missingness,
)
from src.robustez_nome_matching import (
    aplicar_perturbacao,
    recalcular_nome_score,
)

ARQUIVO_BENCHMARK = Path(
    "data/processed/private/ofac_benchmark_individuos.csv"
)

ARQUIVO_RESULTADOS = Path(
    "data/processed/public/matching_robustez_combinada.csv"
)

FIGURA_F1 = Path(
    "reports/figures/matching_robustez_combinada_f1.png"
)

FIGURA_DELTA_AP = Path(
    "reports/figures/matching_valor_incremental_ap.png"
)

NIVEIS_NOME = {
    "Nome limpo": 0,
    "Ruído leve": 1,
    "Ruído moderado": 2,
    "Ruído severo": 3,
}

NIVEIS_CONTEXTO = {
    "Contexto limpo": (0.00, 0.00),
    "30% ausentes": (0.30, 0.00),
    "30% aus. + 10% div.": (0.30, 0.10),
    "50% aus. + 20% div.": (0.50, 0.20),
    "70% aus. + 30% div.": (0.70, 0.30),
}


def criar_consultas_degradadas(
    benchmark: pd.DataFrame,
    intensidade: int,
    seed: int,
) -> pd.Series:
    """Aplica intensidade crescente de ruído aos nomes."""
    rng = np.random.default_rng(seed)

    chaves = (
        benchmark[
            [
                "ofac_id_origem",
                "nome_consulta_normalizado",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "ofac_id_origem",
                "nome_consulta_normalizado",
            ]
        )
    )

    mapa = {}

    for _, linha in chaves.iterrows():
        chave = (
            linha["ofac_id_origem"],
            linha["nome_consulta_normalizado"],
        )

        nome = linha["nome_consulta_normalizado"]

        for _ in range(intensidade):
            nome = aplicar_perturbacao(
                nome,
                "misto",
                rng,
            )

        mapa[chave] = nome

    consultas = [
        mapa[
            (
                linha["ofac_id_origem"],
                linha["nome_consulta_normalizado"],
            )
        ]
        for _, linha in benchmark.iterrows()
    ]

    return pd.Series(
        consultas,
        index=benchmark.index,
    )


def degradar_contexto(
    dados: pd.DataFrame,
    missingness: float,
    divergencia: float,
    seed: int,
) -> pd.DataFrame:
    """Aplica missingness e divergências aos atributos contextuais."""
    resultado = dados.copy()

    if missingness > 0:
        resultado = aplicar_missingness(
            resultado,
            proporcao=missingness,
            seed=seed,
        )

    if divergencia > 0:
        resultado = aplicar_divergencias(
            resultado,
            proporcao=divergencia,
            seed=seed + 100,
        )

    return resultado


def gerar_heatmap(
    matriz: pd.DataFrame,
    titulo: str,
    label: str,
    caminho: Path,
) -> None:
    """Gera heatmap anotado para comparação dos cenários."""
    _, ax = plt.subplots(
        figsize=(10, 6),
    )

    imagem = ax.imshow(
        matriz.to_numpy(dtype=float),
        aspect="auto",
    )

    ax.set_title(titulo)

    ax.set_xticks(
        np.arange(len(matriz.columns))
    )
    ax.set_xticklabels(
        matriz.columns,
        rotation=15,
        ha="right",
    )

    ax.set_yticks(
        np.arange(len(matriz.index))
    )
    ax.set_yticklabels(
        matriz.index
    )

    valores = matriz.to_numpy(dtype=float)

    for linha in range(len(matriz.index)):
        for coluna in range(len(matriz.columns)):
            valor = float(
                valores[linha, coluna]
            )

            ax.text(
                coluna,
                linha,
                f"{valor:.3f}",
                ha="center",
                va="center",
            )

    barra = plt.colorbar(
        imagem,
        ax=ax,
    )

    barra.set_label(label)

    plt.tight_layout()

    plt.savefig(
        caminho,
        dpi=220,
        bbox_inches="tight",
    )

    plt.close()


if __name__ == "__main__":
    df_features = carregar_dados()

    benchmark = pd.read_csv(
        ARQUIVO_BENCHMARK,
        dtype=str,
    ).fillna("")

    benchmark["match_real"] = (
        benchmark["match_real"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    if len(benchmark) != len(df_features):
        raise ValueError(
            "Benchmark e features possuem tamanhos diferentes."
        )

    treino, validacao, teste = separar_amostras(
        df_features
    )

    modelo = LogisticRegression(
        max_iter=1_000,
    )

    modelo.fit(
        treino[FEATURES],
        treino["match_real"],
    )

    scores_validacao = modelo.predict_proba(
        validacao[FEATURES]
    )[:, 1]

    threshold = escolher_threshold(
        validacao["match_real"],
        scores_validacao,
    )

    benchmark_teste = benchmark.loc[
        teste.index
    ].copy()

    resultados = []

    for numero_contexto, (
        nome_contexto,
        (
            missingness,
            divergencia,
        ),
    ) in enumerate(
        NIVEIS_CONTEXTO.items(),
        start=1,
    ):
        teste_contexto = degradar_contexto(
            teste,
            missingness=missingness,
            divergencia=divergencia,
            seed=100 + numero_contexto,
        )

        for numero_nome, (
            nome_ruido,
            intensidade,
        ) in enumerate(
            NIVEIS_NOME.items(),
            start=1,
        ):
            consultas = criar_consultas_degradadas(
                benchmark_teste,
                intensidade=intensidade,
                seed=200 + numero_nome,
            )

            nome_scores = recalcular_nome_score(
                consultas,
                benchmark_teste[
                    "nome_candidato_normalizado"
                ],
            )

            teste_cenario = teste_contexto.copy()

            teste_cenario["nome_score"] = (
                nome_scores
            )

            scores_multi = modelo.predict_proba(
                teste_cenario[FEATURES]
            )[:, 1]

            previsto_multi = (
                scores_multi >= threshold
            )

            ap_nominal = float(
                average_precision_score(
                    teste["match_real"],
                    nome_scores,
                )
            )

            ap_multi = float(
                average_precision_score(
                    teste["match_real"],
                    scores_multi,
                )
            )

            f1_multi = float(
                f1_score(
                    teste["match_real"],
                    previsto_multi,
                    zero_division=0,
                )
            )

            resultados.append(
                {
                    "contexto": nome_contexto,
                    "ruido_nome": nome_ruido,
                    "f1_multivariado": round(
                        f1_multi,
                        4,
                    ),
                    "ap_nominal": round(
                        ap_nominal,
                        4,
                    ),
                    "ap_multivariado": round(
                        ap_multi,
                        4,
                    ),
                    "ganho_ap": round(
                        ap_multi - ap_nominal,
                        4,
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

    FIGURA_F1.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_resultados.to_csv(
        ARQUIVO_RESULTADOS,
        index=False,
    )

    indices_contexto = list(NIVEIS_CONTEXTO.keys())
    colunas_ruido = list(NIVEIS_NOME.keys())

    matriz_f1 = (
        df_resultados.pivot(
            index="contexto",
            columns="ruido_nome",
            values="f1_multivariado",
        )
        .reindex(
            index=indices_contexto,
            columns=colunas_ruido,
        )
    )

    matriz_delta = (
        df_resultados.pivot(
            index="contexto",
            columns="ruido_nome",
            values="ganho_ap",
        )
        .reindex(
            index=indices_contexto,
            columns=colunas_ruido,
        )
    )

    gerar_heatmap(
        matriz_f1,
        titulo=(
            "F1 do modelo multivariado sob "
            "degradação combinada"
        ),
        label="F1",
        caminho=FIGURA_F1,
    )

    gerar_heatmap(
        matriz_delta,
        titulo=(
            "Valor incremental do contexto sobre "
            "a similaridade nominal"
        ),
        label="Ganho de precisão média (ΔAP)",
        caminho=FIGURA_DELTA_AP,
    )

    print("\nF1 multivariado:")
    print(
        matriz_f1.round(3).to_string()
    )

    print("\nGanho de AP sobre similaridade nominal:")
    print(
        matriz_delta.round(3).to_string()
    )

    print(
        "\nFiguras salvas em reports/figures/"
    )
