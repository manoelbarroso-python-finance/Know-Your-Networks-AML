from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
)

from src.avaliacao_matching import (
    FEATURES,
    carregar_dados,
    escolher_threshold,
    separar_amostras,
)

ARQUIVO_BENCHMARK = Path(
    "data/processed/private/ofac_benchmark_individuos.csv"
)

ARQUIVO_RESULTADOS = Path(
    "data/processed/public/matching_robustez_nome.csv"
)

ARQUIVO_FIGURA = Path(
    "reports/figures/matching_robustez_nome.png"
)


def trocar_caracteres(
    nome: str,
    rng: np.random.Generator,
) -> str:
    """Troca dois caracteres adjacentes de um nome."""
    candidatos = [
        indice
        for indice in range(len(nome) - 1)
        if nome[indice].isalnum()
        and nome[indice + 1].isalnum()
    ]

    if not candidatos:
        return nome

    indice = int(rng.choice(candidatos))
    caracteres = list(nome)

    caracteres[indice], caracteres[indice + 1] = (
        caracteres[indice + 1],
        caracteres[indice],
    )

    return "".join(caracteres)


def remover_caractere(
    nome: str,
    rng: np.random.Generator,
) -> str:
    """Remove um caractere alfanumérico do nome."""
    candidatos = [
        indice
        for indice, caractere in enumerate(nome)
        if caractere.isalnum()
    ]

    if len(candidatos) <= 3:
        return trocar_caracteres(nome, rng)

    indice = int(rng.choice(candidatos))

    return nome[:indice] + nome[indice + 1 :]


def remover_token(
    nome: str,
    rng: np.random.Generator,
) -> str:
    """Remove um token do nome quando possível."""
    tokens = nome.split()

    if len(tokens) <= 1:
        return remover_caractere(nome, rng)

    indice = int(rng.integers(0, len(tokens)))

    return " ".join(
        tokens[:indice] + tokens[indice + 1 :]
    )


def aplicar_perturbacao(
    nome: str,
    tipo: str,
    rng: np.random.Generator,
) -> str:
    """Aplica uma perturbação nominal controlada."""
    if tipo == "typo":
        return trocar_caracteres(nome, rng)

    if tipo == "token":
        return remover_token(nome, rng)

    if tipo == "misto":
        funcoes = [
            trocar_caracteres,
            remover_caractere,
            remover_token,
        ]

        funcao = funcoes[
            int(rng.integers(0, len(funcoes)))
        ]

        return funcao(nome, rng)

    return nome


def criar_nomes_perturbados(
    benchmark_teste: pd.DataFrame,
    proporcao: float,
    tipo: str,
    seed: int,
) -> pd.Series:
    """Perturba consultas preservando a mesma alteração por par."""
    rng = np.random.default_rng(seed)

    chaves = (
        benchmark_teste[
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

        if rng.random() < proporcao:
            mapa[chave] = aplicar_perturbacao(
                nome,
                tipo,
                rng,
            )
        else:
            mapa[chave] = nome

    nomes = []

    for _, linha in benchmark_teste.iterrows():
        chave = (
            linha["ofac_id_origem"],
            linha["nome_consulta_normalizado"],
        )

        nomes.append(mapa[chave])

    return pd.Series(
        nomes,
        index=benchmark_teste.index,
    )


def recalcular_nome_score(
    consultas: pd.Series,
    candidatos: pd.Series,
) -> np.ndarray:
    """Recalcula a similaridade nominal após a perturbação."""
    return np.array(
        [
            fuzz.WRatio(consulta, candidato) / 100
            for consulta, candidato in zip(
                consultas,
                candidatos,
                strict=True,
            )
        ]
    )


def avaliar(
    cenario: str,
    metodo: str,
    y_real: pd.Series,
    scores: np.ndarray,
    threshold: float,
) -> dict:
    """Calcula métricas de classificação e ranking."""
    previsto = scores >= threshold

    return {
        "cenario": cenario,
        "metodo": metodo,
        "precision": round(
            float(
                precision_score(
                    y_real,
                    previsto,
                    zero_division=0,
                )
            ),
            4,
        ),
        "recall": round(
            float(
                recall_score(
                    y_real,
                    previsto,
                    zero_division=0,
                )
            ),
            4,
        ),
        "f1": round(
            float(
                f1_score(
                    y_real,
                    previsto,
                    zero_division=0,
                )
            ),
            4,
        ),
        "average_precision": round(
            float(
                average_precision_score(
                    y_real,
                    scores,
                )
            ),
            4,
        ),
    }


def gerar_figura(
    resultados: pd.DataFrame,
) -> None:
    """Compara a robustez do ranking sob ruído nominal."""
    cenarios = resultados["cenario"].drop_duplicates().tolist()
    x = np.arange(len(cenarios))

    _, ax = plt.subplots(
        figsize=(11, 6),
    )

    for metodo in (
        "Similaridade nominal",
        "Modelo multivariado",
    ):
        dados = resultados[
            resultados["metodo"] == metodo
        ]

        ax.plot(
            x,
            dados["average_precision"],
            marker="o",
            linewidth=2,
            label=metodo,
        )

    ax.set_title(
        "Robustez do matching sob degradação nominal"
    )

    ax.set_ylabel("Precisão média (AP)")
    ax.set_xlabel("")

    ax.set_xticks(x)
    ax.set_xticklabels(
        cenarios,
        rotation=15,
        ha="right",
    )

    ax.set_ylim(0, 1.05)

    ax.grid(
        axis="y",
        alpha=0.20,
    )

    ax.legend()

    plt.tight_layout()

    plt.savefig(
        ARQUIVO_FIGURA,
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

    if not benchmark[
        "ofac_id_origem"
    ].reset_index(drop=True).equals(
        df_features[
            "ofac_id_origem"
        ].reset_index(drop=True)
    ):
        raise ValueError(
            "Benchmark e features não estão alinhados."
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

    scores_multi_validacao = modelo.predict_proba(
        validacao[FEATURES]
    )[:, 1]

    threshold_multi = escolher_threshold(
        validacao["match_real"],
        scores_multi_validacao,
    )

    threshold_rapid = escolher_threshold(
        validacao["match_real"],
        validacao["nome_score"].to_numpy(),
    )

    benchmark_teste = benchmark.loc[
        teste.index
    ].copy()

    cenarios = {
        "Baseline limpo": (
            0.00,
            "nenhum",
            42,
        ),
        "25% com typo": (
            0.25,
            "typo",
            43,
        ),
        "50% com typo": (
            0.50,
            "typo",
            44,
        ),
        "30% com token ausente": (
            0.30,
            "token",
            45,
        ),
        "50% com ruído misto": (
            0.50,
            "misto",
            46,
        ),
    }

    resultados = []

    for nome_cenario, (
        proporcao,
        tipo,
        seed,
    ) in cenarios.items():
        consultas = criar_nomes_perturbados(
            benchmark_teste,
            proporcao,
            tipo,
            seed,
        )

        nome_scores = recalcular_nome_score(
            consultas,
            benchmark_teste[
                "nome_candidato_normalizado"
            ],
        )

        teste_cenario = teste.copy()
        teste_cenario["nome_score"] = nome_scores

        scores_multi = modelo.predict_proba(
            teste_cenario[FEATURES]
        )[:, 1]

        resultados.append(
            avaliar(
                nome_cenario,
                "Similaridade nominal",
                teste["match_real"],
                nome_scores,
                threshold_rapid,
            )
        )

        resultados.append(
            avaliar(
                nome_cenario,
                "Modelo multivariado",
                teste["match_real"],
                scores_multi,
                threshold_multi,
            )
        )

    df_resultados = pd.DataFrame(resultados)

    ARQUIVO_RESULTADOS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARQUIVO_FIGURA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_resultados.to_csv(
        ARQUIVO_RESULTADOS,
        index=False,
    )

    gerar_figura(df_resultados)

    print("\nResultados — robustez nominal:")
    print(
        df_resultados.to_string(
            index=False
        )
    )

    print(
        "\nFigura salva em: "
        "reports/figures/matching_robustez_nome.png"
    )
