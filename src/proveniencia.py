from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class Proveniencia:
    """Registra a origem e o momento de coleta de um dado externo."""

    fonte: str
    conjunto_dados: str
    coletado_em: datetime
    id_registro_origem: str | None = None
    atualizado_na_fonte: str | None = None
    versao_fonte: str | None = None

    @classmethod
    def criar(
        cls,
        fonte: str,
        conjunto_dados: str,
        id_registro_origem: str | None = None,
        atualizado_na_fonte: str | None = None,
        versao_fonte: str | None = None,
    ) -> "Proveniencia":
        return cls(
            fonte=fonte,
            conjunto_dados=conjunto_dados,
            coletado_em=datetime.now(UTC),
            id_registro_origem=id_registro_origem,
            atualizado_na_fonte=atualizado_na_fonte,
            versao_fonte=versao_fonte,
        )
