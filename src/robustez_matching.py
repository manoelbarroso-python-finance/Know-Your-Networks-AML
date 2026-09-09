from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit

ARQUIVO_FEATURES = Path(
    "data/processed/private/ofac_matching_features.csv"
)

ARQUIVO_RESULTADOS = Path(
    "data/processed/public/matching_robustez_metricas.csv"
)

ARQUIVO_FIGURA = Path(
    "reports/figures/matching_robustez.png"
)

FEATURES = [
    "nome_score",
    "nascimento_observado",
    "nascimento_match",
    "local_observado",
    "local_match",
    "nacionalidade_observada",
    "nacionalidade_match",
    "cidadania_observada",
    "cidadania_match",
    "documento_observado",
    "documento_match",
]

EVIDENCIAS = [
    ("nascimento_observado", "nascimento_match"),
    ("local_observado", "local_match"),
    ("nacionalidade_observada", "nacionalidade_match"),
    ("cidadania_observada", "cidadania_match"),
    ("documento_observado", "documento_match"),
]


def carregar_dados() -> pd.DataFrame:
    """Carrega e prepara as features do benchmark."""
    dados = pd.read_csv(
        ARQUIVO_FEATURES,
        dtype={
            "ofac_id_origem": str,
            "ofac_id_candidato": str,
        },
    )

    dados["match_real"] = (
        dados["match_real"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    for coluna in FEATURES:
        dados[coluna] = pd.to_numeric(
            dados[coluna],
            errors="coerce",
        ).fillna(0)

    return dados


def separar_amostras(
    dados: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Reproduz o split por entidade usado na avaliação base."""
    primeira_divisao = GroupShuffleSplit(
        n_splits=1,
        train_size=0.60,
        random_state=42,
    )

    treino_idx, temporario_idx = next(
        primeira_divisao.split(
            dados,
            groups=dados["ofac_id_origem"],
        )
    )

    treino = dados.iloc[treino_idx].copy()
    temporario = dados.iloc[temporario_idx].copy()

    segunda_divisao = GroupShuffleSplit(
        n_splits=1,
        train_size=0.50,
        random_state=42,
    )

    validacao_idx, teste_idx = next(
        segunda_divisao.split(
            temporario,
            groups=temporario["ofac_id_origem"],
        )
    )

    validacao = temporario.iloc[validacao_idx].copy()
    teste = temporario.iloc[teste_idx].copy()

    return treino, validacao, teste


def escolher_threshold(
    y_real: pd.Series,
    scores: np.ndarray,
) -> float:
    """Escolhe o threshold que maximiza F1 na validação limpa."""
    melhor_threshold = 0.0
    melhor_f1 = -1.0

    for threshold in np.linspace(0, 1, 201):
        previsto = scores >= threshold

        f1 = float(
            f1_score(
                y_real,
                previsto,
                zero_division=0,
            )
        )

        if f1 > melhor_f1:
            melhor_f1 = f1
            melhor_threshold = float(threshold)

    return melhor_threshold


def remover_documentos(
    dados: pd.DataFrame,
) -> pd.DataFrame:
    """Simula indisponibilidade completa de documentos."""
    resultado = dados.copy()

    resultado["documento_observado"] = 0
    resultado["documento_match"] = 0

    return resultado


def aplicar_missingness(
    dados: pd.DataFrame,
    proporcao: float,
    seed: int,
) -> pd.DataFrame:
    """Remove aleatoriamente parte dos atributos observados."""
    resultado = dados.copy()
    rng = np.random.default_rng(seed)

    for observado, match in EVIDENCIAS:
        mascara = (
            resultado[observado].eq(1).to_numpy()
            & (rng.random(len(resultado)) < proporcao)
        )

        resultado.loc[mascara, observado] = 0
        resultado.loc[mascara, match] = 0

    return resultado


def aplicar_divergencias(
    dados: pd.DataFrame,
    proporcao: float,
    seed: int,
) -> pd.DataFrame:
    """Introduz divergências controladas em pares positivos."""
    resultado = dados.copy()
    rng = np.random.default_rng(seed)

    positivos = resultado["match_real"].eq(True)

    for observado, match in EVIDENCIAS:
        elegiveis = (
            positivos
            & resultado[observado].eq(1)
            & resultado[match].eq(1)
        )

        mascara = (
            elegiveis.to_numpy()
            & (rng.random(len(resultado)) < proporcao)
        )

        resultado.loc[mascara, match] = 0

    return resultado


def criar_cenarios(
    teste: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Constrói cenários progressivamente mais adversos."""
    missing_30 = aplicar_missingness(
        teste,
        proporcao=0.30,
        seed=42,
    )

    missing_30_div_10 = aplicar_divergencias(
        missing_30,
        proporcao=0.10,
        seed=43,
    )

    missing_50 = aplicar_missingness(
        teste,
        proporcao=0.50,
        seed=44,
    )

    missing_50_div_20 = aplicar_divergencias(
        missing_50,
        proporcao=0.20,
        seed=45,
    )

    return {
        "Baseline limpo": teste.copy(),
        "Sem documentos": remover_documentos(teste),
        "30% campos ausentes": missing_30,
        "30% ausentes + 10% divergentes": missing_30_div_10,
        "50% ausentes + 20% divergentes": missing_50_div_20,
    }


def avaliar_cenario(
    nome: str,
    dados: pd.DataFrame,
    modelo: LogisticRegression,
    threshold: float,
) -> dict:
    """Avalia o modelo congelado em um cenário de robustez."""
    y_real = dados["match_real"]

    scores = modelo.predict_proba(
        dados[FEATURES]
    )[:, 1]

    previsto = scores >= threshold

    return {
        "cenario": nome,
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
    f1_rapidfuzz: float,
) -> None:
    """Mostra a deterioração do modelo sob estresse."""
    x = np.arange(len(resultados))

    _, ax = plt.subplots(
        figsize=(11, 6),
    )

    ax.plot(
        x,
        resultados["f1"],
        marker="o",
        linewidth=2,
        label="F1 — modelo multivariado",
    )

    ax.plot(
        x,
        resultados["average_precision"],
        marker="o",
        linewidth=2,
        label="Precisão média — modelo multivariado",
    )

    ax.axhline(
        y=f1_rapidfuzz,
        linestyle="--",
        linewidth=1.5,
        label=f"F1 — similaridade nominal ({f1_rapidfuzz:.2f})",
    )

    ax.set_title(
        "Robustez do modelo multivariado sob degradação dos dados"
    )

    ax.set_ylabel("Valor da métrica")
    ax.set_xlabel("")

    ax.set_xticks(x)
    ax.set_xticklabels(
        resultados["cenario"],
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
    df = carregar_dados()

    treino, validacao, teste = separar_amostras(df)

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

    rapid_validacao = validacao["nome_score"].to_numpy()

    threshold_rapid = escolher_threshold(
        validacao["match_real"],
        rapid_validacao,
    )

    rapid_teste = teste["nome_score"].to_numpy()

    previsto_rapid = rapid_teste >= threshold_rapid

    f1_rapid = float(
        f1_score(
            teste["match_real"],
            previsto_rapid,
            zero_division=0,
        )
    )

    cenarios = criar_cenarios(teste)

    resultados = pd.DataFrame(
        [
            avaliar_cenario(
                nome,
                dados,
                modelo,
                threshold,
            )
            for nome, dados in cenarios.items()
        ]
    )

    ARQUIVO_RESULTADOS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARQUIVO_FIGURA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    resultados.to_csv(
        ARQUIVO_RESULTADOS,
        index=False,
    )

    gerar_figura(
        resultados,
        f1_rapid,
    )

    print(
        f"\nThreshold multivariado congelado: "
        f"{threshold:.3f}"
    )

    print(
        f"F1 da similaridade nominal: "
        f"{f1_rapid:.4f}"
    )

    print("\nResultados de robustez:")
    print(resultados.to_string(index=False))

    print(
        "\nFigura salva em: "
        "reports/figures/matching_robustez.png"
    )
