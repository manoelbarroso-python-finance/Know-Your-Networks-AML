from dataclasses import FrozenInstanceError
from datetime import UTC

import pytest

from src.proveniencia import Proveniencia


def test_criar_proveniencia():
    proveniencia = Proveniencia.criar(
        fonte="OFAC",
        conjunto_dados="SDN",
        id_registro_origem="12345",
    )

    assert proveniencia.fonte == "OFAC"
    assert proveniencia.conjunto_dados == "SDN"
    assert proveniencia.id_registro_origem == "12345"
    assert proveniencia.coletado_em.tzinfo == UTC


def test_proveniencia_e_imutavel():
    proveniencia = Proveniencia.criar(
        fonte="OFAC",
        conjunto_dados="SDN",
    )

    with pytest.raises(FrozenInstanceError):
        proveniencia.fonte = "Outra fonte"
