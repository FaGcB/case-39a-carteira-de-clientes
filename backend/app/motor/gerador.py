import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

PARCELAS = (12, 24, 36, 48, 60, 72, 84)
VALOR_MIN, VALOR_MAX, PASSO_VALOR = 1_000, 60_000, 100
TAXA_MIN, TAXA_MAX = Decimal("0.0149"), Decimal("0.0329")


@dataclass(frozen=True)
class Proposta:
    cpf: str
    valor: Decimal
    parcelas: int
    taxa_mensal: Decimal
    gerado_em: datetime


class MotorDeCredito(Protocol):
    def consultar(self, cpf: str) -> Proposta: ...


def _inteiro(dados: bytes) -> int:
    return int.from_bytes(dados, "big")


def gerar_proposta(cpf: str, agora: datetime | None = None) -> Proposta:
    h = hashlib.sha256(cpf.encode()).digest()
    passos_valor = (VALOR_MAX - VALOR_MIN) // PASSO_VALOR + 1
    valor = VALOR_MIN + (_inteiro(h[0:8]) % passos_valor) * PASSO_VALOR
    parcelas = PARCELAS[_inteiro(h[8:16]) % len(PARCELAS)]
    passos_taxa = int((TAXA_MAX - TAXA_MIN) * 10_000) + 1
    taxa = TAXA_MIN + Decimal(_inteiro(h[16:24]) % passos_taxa) / 10_000
    return Proposta(
        cpf=cpf,
        valor=Decimal(valor).quantize(Decimal("0.01")),
        parcelas=parcelas,
        taxa_mensal=taxa.quantize(Decimal("0.0001")),
        gerado_em=agora or datetime.now(UTC),
    )


class MotorSimulado:
    def consultar(self, cpf: str) -> Proposta:
        return gerar_proposta(cpf)
