from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit

ARQUIVO_FEATURES = Path(
    "data/processed/private/ofac_matching_features.csv"
)

PASTA_PUBLICA = Path("data/processed/public")
PASTA_FIGURAS = Path("reports/figures")

ARQUIVO_METRICAS = PASTA_PUBLICA / "matching_metricas.csv"
ARQUIVO_COEFICIENTES = PASTA_PUBLICA / "matching_coeficientes_logit.csv"

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


def carregar_dados() -> pd.DataFrame:
    """Carrega e prepara o benchmark para avaliação."""
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
    """Separa treino, validação e teste por entidade de origem."""
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
    """Seleciona o threshold que maximiza F1 na validação."""
    melhor_threshold = 0.0
    melhor_f1 = -1.0

    for threshold in np.linspace(0, 1, 201):
        previsto = scores >= threshold

        f1 = f1_score(
            y_real,
            previsto,
            zero_division=0,
        )

        if f1 > melhor_f1:
            melhor_f1 = f1
            melhor_threshold = float(threshold)

    return melhor_threshold


def calcular_metricas(
    metodo: str,
    y_real: pd.Series,
    scores: np.ndarray,
    threshold: float,
) -> dict:
    """Calcula métricas de classificação para um método."""
    previsto = scores >= threshold

    matriz = confusion_matrix(
        y_real,
        previsto,
    )

    tn, fp, fn, tp = (
        int(valor)
        for valor in matriz.ravel()
    )

    return {
        "metodo": metodo,
        "threshold": round(float(threshold), 3),
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
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


def gerar_figura_metricas(
    metricas: pd.DataFrame,
) -> None:
    """Gera comparação visual das métricas de classificação."""
    mapa_metodos = {
        "Exact Match": "Correspondência exata",
        "RapidFuzz": "Similaridade nominal",
        "Multivariado": "Modelo multivariado",
    }

    metricas_plot = metricas.copy()

    metricas_plot["metodo"] = (
        metricas_plot["metodo"]
        .map(mapa_metodos)
    )

    metodos = metricas_plot["metodo"].tolist()

    precisao = metricas_plot["precision"].to_numpy(
        dtype=float
    )

    recall = metricas_plot["recall"].to_numpy(
        dtype=float
    )

    f1 = metricas_plot["f1"].to_numpy(
        dtype=float
    )

    x = np.arange(len(metodos))
    largura = 0.22

    _, ax = plt.subplots(
        figsize=(10, 6)
    )

    barras_precisao = ax.bar(
        x - largura,
        precisao,
        largura,
        label="Precisão",
    )

    barras_recall = ax.bar(
        x,
        recall,
        largura,
        label="Recall",
    )

    barras_f1 = ax.bar(
        x + largura,
        f1,
        largura,
        label="F1",
    )

    for barras, valores in (
        (barras_precisao, precisao),
        (barras_recall, recall),
        (barras_f1, f1),
    ):
        for barra, valor in zip(
            barras,
            valores,
            strict=True,
        ):
            if valor <= 0:
                continue

            ax.text(
                barra.get_x() + barra.get_width() / 2,
                valor + 0.015,
                f"{valor:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    # Exact Match possui zero nas três métricas.
    ax.text(
        x[0],
        0.035,
        "Todas = 0,00",
        ha="center",
        va="bottom",
        fontsize=9,
    )

    ax.set_title(
        "Desempenho dos métodos de entity matching — OFAC"
    )

    ax.set_ylabel("Valor da métrica")
    ax.set_xlabel("")

    ax.set_xticks(x)
    ax.set_xticklabels(metodos)

    ax.set_ylim(0, 1.10)

    ax.legend(
        title="Métrica",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )

    ax.grid(
        axis="y",
        alpha=0.20,
    )

    plt.tight_layout()

    plt.savefig(
        PASTA_FIGURAS / "matching_comparacao_metricas.png",
        dpi=220,
        bbox_inches="tight",
    )

    plt.close()


def gerar_curva_pr(
    y_real: pd.Series,
    rapid_scores: np.ndarray,
    multi_scores: np.ndarray,
) -> None:
    """Gera curva Precision-Recall dos métodos contínuos."""
    precision_rapid, recall_rapid, _ = precision_recall_curve(
        y_real,
        rapid_scores,
    )

    precision_multi, recall_multi, _ = precision_recall_curve(
        y_real,
        multi_scores,
    )

    ap_rapid = float(
        average_precision_score(
            y_real,
            rapid_scores,
        )
    )

    ap_multi = float(
        average_precision_score(
            y_real,
            multi_scores,
        )
    )

    _, ax = plt.subplots(figsize=(8.5, 6))

    ax.plot(
        recall_rapid,
        precision_rapid,
        linewidth=2,
        label=f"Similaridade nominal — AP = {ap_rapid:.3f}",
    )

    ax.plot(
        recall_multi,
        precision_multi,
        linewidth=2,
        label=f"Modelo multivariado — AP = {ap_multi:.3f}",
    )

    ax.axhline(
        y=float(y_real.mean()),
        linestyle="--",
        linewidth=1.5,
        label="Baseline aleatória",
    )

    ax.set_title(
        "Curva Precisão–Recall — benchmark de matching"
    )
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precisão")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower left", frameon=True)

    plt.tight_layout()

    plt.savefig(
        PASTA_FIGURAS / "matching_curva_precision_recall.png",
        dpi=220,
        bbox_inches="tight",
    )

    plt.close()


def salvar_coeficientes(
    modelo: LogisticRegression,
) -> None:
    """Salva coeficientes do modelo multivariado."""
    coeficientes = pd.DataFrame(
        {
            "feature": FEATURES,
            "coeficiente": modelo.coef_[0],
            "odds_ratio": np.exp(modelo.coef_[0]),
        }
    )

    coeficientes["abs_coeficiente"] = (
        coeficientes["coeficiente"].abs()
    )

    coeficientes = coeficientes.sort_values(
        "abs_coeficiente",
        ascending=False,
    )

    coeficientes.to_csv(
        ARQUIVO_COEFICIENTES,
        index=False,
    )


if __name__ == "__main__":
    df = carregar_dados()

    treino, validacao, teste = separar_amostras(df)

    x_treino = treino[FEATURES]
    y_treino = treino["match_real"]

    x_validacao = validacao[FEATURES]
    y_validacao = validacao["match_real"]

    x_teste = teste[FEATURES]
    y_teste = teste["match_real"]

    modelo = LogisticRegression(
        max_iter=1_000,
    )

    modelo.fit(
        x_treino,
        y_treino,
    )

    rapid_validacao = validacao["nome_score"].to_numpy()

    threshold_rapid = escolher_threshold(
        y_validacao,
        rapid_validacao,
    )

    multi_validacao = modelo.predict_proba(
        x_validacao
    )[:, 1]

    threshold_multi = escolher_threshold(
        y_validacao,
        multi_validacao,
    )

    exact_scores = (
        teste["nome_score"]
        .eq(1.0)
        .astype(float)
        .to_numpy()
    )

    rapid_scores = teste["nome_score"].to_numpy()

    multi_scores = modelo.predict_proba(
        x_teste
    )[:, 1]

    resultados = [
        calcular_metricas(
            "Exact Match",
            y_teste,
            exact_scores,
            1.0,
        ),
        calcular_metricas(
            "RapidFuzz",
            y_teste,
            rapid_scores,
            threshold_rapid,
        ),
        calcular_metricas(
            "Multivariado",
            y_teste,
            multi_scores,
            threshold_multi,
        ),
    ]

    df_metricas = pd.DataFrame(resultados)

    PASTA_PUBLICA.mkdir(
        parents=True,
        exist_ok=True,
    )

    PASTA_FIGURAS.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_metricas.to_csv(
        ARQUIVO_METRICAS,
        index=False,
    )

    salvar_coeficientes(modelo)

    gerar_figura_metricas(df_metricas)

    gerar_curva_pr(
        y_teste,
        rapid_scores,
        multi_scores,
    )

    print("\nTamanho das amostras:")
    print(f"Treino:     {len(treino):,}")
    print(f"Validação:  {len(validacao):,}")
    print(f"Teste:      {len(teste):,}")

    print("\nThresholds escolhidos na validação:")
    print(f"RapidFuzz:   {threshold_rapid:.3f}")
    print(f"Multivariado: {threshold_multi:.3f}")

    print("\nResultados no conjunto de teste:")
    print(df_metricas.to_string(index=False))

    print(
        "\nFiguras salvas em reports/figures/"
    )
