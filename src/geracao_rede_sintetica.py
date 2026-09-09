from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

PASTA_SAIDA = Path("data/synthetic")

SEED = 42

N_PESSOAS = 100
N_EMPRESAS = 25
N_DISPOSITIVOS = 30
N_ENDERECOS = 35
N_RISK_ENTITIES = 5

PAISES = [
    "Brasil",
    "Argentina",
    "Chile",
    "México",
    "Estados Unidos",
    "Reino Unido",
    "Espanha",
    "Portugal",
]


def criar_ids(
    prefixo: str,
    quantidade: int,
) -> list[str]:
    """Cria identificadores sintéticos sequenciais."""
    return [
        f"{prefixo}_{numero:03d}"
        for numero in range(1, quantidade + 1)
    ]


def gerar_pessoas(
    fake: Faker,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Gera clientes sintéticos."""
    ids = criar_ids("PERSON", N_PESSOAS)

    return pd.DataFrame(
        {
            "person_id": ids,
            "nome": [
                fake.unique.name()
                for _ in ids
            ],
            "pais": rng.choice(
                PAISES,
                size=len(ids),
            ),
            "segmento": rng.choice(
                [
                    "Varejo",
                    "Alta renda",
                    "Empresarial",
                ],
                size=len(ids),
                p=[0.65, 0.20, 0.15],
            ),
            "sintetico": True,
        }
    )


def gerar_empresas(
    fake: Faker,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Gera empresas sintéticas."""
    ids = criar_ids("COMPANY", N_EMPRESAS)

    return pd.DataFrame(
        {
            "company_id": ids,
            "nome": [
                fake.unique.company()
                for _ in ids
            ],
            "jurisdicao": rng.choice(
                PAISES,
                size=len(ids),
            ),
            "sintetico": True,
        }
    )


def gerar_dispositivos() -> pd.DataFrame:
    """Gera dispositivos sintéticos."""
    ids = criar_ids(
        "DEVICE",
        N_DISPOSITIVOS,
    )

    return pd.DataFrame(
        {
            "device_id": ids,
            "tipo": [
                "mobile" if numero % 3 else "desktop"
                for numero in range(1, len(ids) + 1)
            ],
            "sintetico": True,
        }
    )


def gerar_enderecos(
    fake: Faker,
) -> pd.DataFrame:
    """Gera endereços sintéticos."""
    ids = criar_ids(
        "ADDRESS",
        N_ENDERECOS,
    )

    return pd.DataFrame(
        {
            "address_id": ids,
            "descricao": [
                fake.address().replace("\n", ", ")
                for _ in ids
            ],
            "sintetico": True,
        }
    )


def gerar_entidades_risco() -> pd.DataFrame:
    """Gera referências sintéticas de risco."""
    ids = criar_ids(
        "RISK",
        N_RISK_ENTITIES,
    )

    return pd.DataFrame(
        {
            "risk_id": ids,
            "nome": [
                f"Risk Reference {numero}"
                for numero in range(
                    1,
                    N_RISK_ENTITIES + 1,
                )
            ],
            "fonte": "OFAC",
            "categoria": "Sanctions reference",
            "sintetico": True,
        }
    )


def gerar_contas(
    pessoas: pd.DataFrame,
    empresas: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict]]:
    """Gera contas e relações de propriedade."""
    contas = []
    relacoes = []

    contador = 1

    for person_id in pessoas["person_id"]:
        account_id = f"ACCOUNT_{contador:03d}"
        contador += 1

        contas.append(
            {
                "account_id": account_id,
                "tipo": "Pessoa física",
                "moeda": "USD",
                "sintetico": True,
            }
        )

        relacoes.append(
            {
                "origem": person_id,
                "destino": account_id,
                "tipo": "OWNS",
                "contexto": "propriedade de conta",
            }
        )

    for company_id in empresas["company_id"]:
        account_id = f"ACCOUNT_{contador:03d}"
        contador += 1

        contas.append(
            {
                "account_id": account_id,
                "tipo": "Pessoa jurídica",
                "moeda": "USD",
                "sintetico": True,
            }
        )

        relacoes.append(
            {
                "origem": company_id,
                "destino": account_id,
                "tipo": "OWNS",
                "contexto": "propriedade de conta",
            }
        )

    return pd.DataFrame(contas), relacoes


def gerar_relacoes_base(
    pessoas: pd.DataFrame,
    empresas: pd.DataFrame,
    dispositivos: pd.DataFrame,
    enderecos: pd.DataFrame,
    rng: np.random.Generator,
) -> list[dict]:
    """Gera relacionamentos normais da rede."""
    relacoes = []

    device_ids = dispositivos["device_id"].tolist()
    address_ids = enderecos["address_id"].tolist()

    for person_id in pessoas["person_id"]:
        relacoes.append(
            {
                "origem": person_id,
                "destino": str(
                    rng.choice(device_ids)
                ),
                "tipo": "USES_DEVICE",
                "contexto": "uso de dispositivo",
            }
        )

        relacoes.append(
            {
                "origem": person_id,
                "destino": str(
                    rng.choice(address_ids)
                ),
                "tipo": "LIVES_AT",
                "contexto": "endereço cadastrado",
            }
        )

    for company_id in empresas["company_id"]:
        relacoes.append(
            {
                "origem": company_id,
                "destino": str(
                    rng.choice(address_ids)
                ),
                "tipo": "REGISTERED_AT",
                "contexto": "endereço societário",
            }
        )

    return relacoes


def inserir_ground_truth(
    relacoes: list[dict],
) -> pd.DataFrame:
    """Insere padrões investigativos conhecidos na rede."""
    padroes = []

    # 1. Exposição direta.
    relacoes.append(
        {
            "origem": "PERSON_001",
            "destino": "RISK_001",
            "tipo": "MATCHED_TO",
            "contexto": "screening direto",
        }
    )

    padroes.append(
        {
            "pattern_id": "GT_001",
            "tipo": "Exposição direta",
            "descricao": (
                "PERSON_001 possui conexão direta "
                "com RISK_001."
            ),
        }
    )

    # 2. Exposição indireta via empresa.
    relacoes.extend(
        [
            {
                "origem": "PERSON_002",
                "destino": "COMPANY_001",
                "tipo": "CONTROLS",
                "contexto": "controle societário",
            },
            {
                "origem": "COMPANY_001",
                "destino": "RISK_002",
                "tipo": "MATCHED_TO",
                "contexto": "screening corporativo",
            },
        ]
    )

    padroes.append(
        {
            "pattern_id": "GT_002",
            "tipo": "Exposição indireta",
            "descricao": (
                "PERSON_002 alcança RISK_002 "
                "por meio de COMPANY_001."
            ),
        }
    )

    # 3. Dispositivo compartilhado como ponte.
    for person_id in [
        "PERSON_003",
        "PERSON_004",
        "PERSON_005",
    ]:
        relacoes.append(
            {
                "origem": person_id,
                "destino": "DEVICE_001",
                "tipo": "USES_DEVICE",
                "contexto": "dispositivo compartilhado",
            }
        )

    relacoes.append(
        {
            "origem": "PERSON_005",
            "destino": "RISK_003",
            "tipo": "MATCHED_TO",
            "contexto": "screening direto",
        }
    )

    padroes.append(
        {
            "pattern_id": "GT_003",
            "tipo": "Ponte por dispositivo",
            "descricao": (
                "PERSON_003 e PERSON_004 "
                "compartilham DEVICE_001 com "
                "PERSON_005, conectado a RISK_003."
            ),
        }
    )

    # 4. Exposição por endereço e empresa.
    relacoes.extend(
        [
            {
                "origem": "PERSON_006",
                "destino": "ADDRESS_001",
                "tipo": "LIVES_AT",
                "contexto": "endereço compartilhado",
            },
            {
                "origem": "COMPANY_002",
                "destino": "ADDRESS_001",
                "tipo": "REGISTERED_AT",
                "contexto": "endereço compartilhado",
            },
            {
                "origem": "COMPANY_002",
                "destino": "RISK_004",
                "tipo": "MATCHED_TO",
                "contexto": "screening corporativo",
            },
        ]
    )

    padroes.append(
        {
            "pattern_id": "GT_004",
            "tipo": "Ponte por endereço",
            "descricao": (
                "PERSON_006 compartilha endereço "
                "com COMPANY_002, conectada a RISK_004."
            ),
        }
    )

    # 5. Hub legítimo para controle de falso positivo.
    for person_id in [
        "PERSON_020",
        "PERSON_021",
        "PERSON_022",
        "PERSON_023",
        "PERSON_024",
        "PERSON_025",
    ]:
        relacoes.append(
            {
                "origem": person_id,
                "destino": "ADDRESS_035",
                "tipo": "LIVES_AT",
                "contexto": "endereço coletivo legítimo",
            }
        )

    padroes.append(
        {
            "pattern_id": "GT_005",
            "tipo": "Hub legítimo",
            "descricao": (
                "ADDRESS_035 conecta vários clientes, "
                "mas não possui exposição a risco."
            ),
        }
    )

    return pd.DataFrame(padroes)


def validar_ids(
    tabelas: list[pd.DataFrame],
) -> None:
    """Valida unicidade dos identificadores sintéticos."""
    ids = []

    for tabela in tabelas:
        primeira_coluna = tabela.columns[0]
        ids.extend(
            tabela[primeira_coluna]
            .astype(str)
            .tolist()
        )

    if len(ids) != len(set(ids)):
        raise ValueError(
            "Foram encontrados IDs sintéticos duplicados."
        )


def salvar_dados(
    pessoas: pd.DataFrame,
    empresas: pd.DataFrame,
    contas: pd.DataFrame,
    dispositivos: pd.DataFrame,
    enderecos: pd.DataFrame,
    riscos: pd.DataFrame,
    relacoes: pd.DataFrame,
    ground_truth: pd.DataFrame,
) -> None:
    """Salva os datasets sintéticos."""
    PASTA_SAIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivos = {
        "pessoas.csv": pessoas,
        "empresas.csv": empresas,
        "contas.csv": contas,
        "dispositivos.csv": dispositivos,
        "enderecos.csv": enderecos,
        "entidades_risco.csv": riscos,
        "relacoes.csv": relacoes,
        "ground_truth_rede.csv": ground_truth,
    }

    for nome, dados in arquivos.items():
        dados.to_csv(
            PASTA_SAIDA / nome,
            index=False,
            encoding="utf-8",
        )


if __name__ == "__main__":
    Faker.seed(SEED)

    fake = Faker("pt_BR")
    fake.seed_instance(SEED)

    rng = np.random.default_rng(SEED)

    df_pessoas = gerar_pessoas(
        fake,
        rng,
    )

    df_empresas = gerar_empresas(
        fake,
        rng,
    )

    df_dispositivos = gerar_dispositivos()

    df_enderecos = gerar_enderecos(
        fake
    )

    df_riscos = gerar_entidades_risco()

    df_contas, relacoes = gerar_contas(
        df_pessoas,
        df_empresas,
    )

    relacoes.extend(
        gerar_relacoes_base(
            df_pessoas,
            df_empresas,
            df_dispositivos,
            df_enderecos,
            rng,
        )
    )

    df_ground_truth = inserir_ground_truth(
        relacoes
    )

    df_relacoes = (
        pd.DataFrame(relacoes)
        .drop_duplicates()
        .reset_index(drop=True)
    )

    validar_ids(
        [
            df_pessoas,
            df_empresas,
            df_contas,
            df_dispositivos,
            df_enderecos,
            df_riscos,
        ]
    )

    salvar_dados(
        df_pessoas,
        df_empresas,
        df_contas,
        df_dispositivos,
        df_enderecos,
        df_riscos,
        df_relacoes,
        df_ground_truth,
    )

    print("\nRede sintética gerada.")

    print(f"Pessoas:          {len(df_pessoas):,}")
    print(f"Empresas:         {len(df_empresas):,}")
    print(f"Contas:           {len(df_contas):,}")
    print(f"Dispositivos:     {len(df_dispositivos):,}")
    print(f"Endereços:        {len(df_enderecos):,}")
    print(f"Entidades risco:  {len(df_riscos):,}")
    print(f"Relacionamentos:  {len(df_relacoes):,}")

    print("\nPadrões de ground truth:")
    print(
        df_ground_truth[
            [
                "pattern_id",
                "tipo",
            ]
        ].to_string(index=False)
    )

    print(
        "\nArquivos salvos em: data/synthetic/"
    )
