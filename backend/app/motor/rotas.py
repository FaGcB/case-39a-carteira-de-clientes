from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.config import config
from app.erros import ErroApi
from app.importacao.normalizacao import cpf_valido, somente_digitos
from app.motor.gerador import MotorDeCredito, MotorSimulado
from app.motor.limitador import JanelaDeslizante
from app.schemas import PropostaOut

router = APIRouter(prefix="/api/motor", tags=["motor de crédito"])


@lru_cache
def get_motor() -> MotorDeCredito:
    return MotorSimulado()


@lru_cache
def get_limitador() -> JanelaDeslizante:
    return JanelaDeslizante(limite=config.motor_limite_por_minuto, janela=60)


def _origem(request: Request) -> str:
    encaminhado = request.headers.get("x-forwarded-for")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


@router.get("/proposta", response_model=PropostaOut)
def proposta(
    request: Request,
    motor: Annotated[MotorDeCredito, Depends(get_motor)],
    limitador: Annotated[JanelaDeslizante, Depends(get_limitador)],
    cpf: Annotated[str, Query(max_length=20)],
) -> PropostaOut:
    espera = limitador.registrar(_origem(request))
    if espera is not None:
        raise ErroApi(
            429,
            f"O motor de crédito atingiu o limite de {limitador.limite} consultas por minuto.",
            headers={"Retry-After": str(espera)},
        )
    digitos = somente_digitos(cpf)
    if not cpf_valido(digitos):
        raise ErroApi(400, "CPF inválido.", {"cpf": "Informe um CPF válido, com 11 dígitos."})
    p = motor.consultar(digitos)
    return PropostaOut(
        cpf=p.cpf, valor=float(p.valor), parcelas=p.parcelas, taxa_mensal=float(p.taxa_mensal), gerado_em=p.gerado_em
    )
