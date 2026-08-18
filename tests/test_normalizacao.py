import pytest

from src.normalizacao import normalizar_data, normalizar_nome


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


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("1980-03-15", ("1980-03-15", "dia")),
        ("15/03/1980", ("1980-03-15", "dia")),
        ("15-03-1980", ("1980-03-15", "dia")),
        ("1980-03", ("1980-03", "mes")),
        ("1980", ("1980", "ano")),
        ("", ("", "ausente")),
        (None, ("", "ausente")),
        ("31/02/1980", ("", "invalida")),
    ],
)
def test_normalizar_data(entrada, esperado):
    assert normalizar_data(entrada) == esperado
