import pytest

from src.normalizacao import normalizar_nome


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("João da Silva", "joao da silva"),
        (" JOÃO   DA SILVA ", "joao da silva"),
        ("João-da-Silva", "joao da silva"),
        ("José D'Ávila", "jose d avila"),
        ("Maria dos Santos", "maria dos santos"),
        (None, ""),
    ],
)
def test_normalizar_nome(entrada, esperado):
    assert normalizar_nome(entrada) == esperado


def test_normalizacao_e_idempotente():
    nome = " João-da-Silva "
    normalizado = normalizar_nome(nome)

    assert normalizar_nome(normalizado) == normalizado
