from datetime import date
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import AlteracaoCliente

ROTULOS = {
    "nome": "Nome",
    "data_nascimento": "Data de nascimento",
    "sexo": "Sexo",
    "estado_civil": "Estado civil",
    "email": "E-mail",
    "telefone": "Telefone",
    "cep": "CEP",
    "logradouro": "Logradouro",
    "numero": "Número",
    "complemento": "Complemento",
    "bairro": "Bairro",
    "cidade": "Cidade",
    "uf": "UF",
    "cargo": "Cargo",
    "data_admissao": "Data de admissão",
    "salario_bruto": "Salário bruto",
    "margem_disponivel": "Margem disponível",
    "vinculo": "Novo vínculo",
}

CAMPOS_CADASTRO = (
    "nome",
    "data_nascimento",
    "sexo",
    "estado_civil",
    "email",
    "telefone",
    "cep",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cidade",
    "uf",
)
CAMPOS_VINCULO = ("cargo", "data_admissao", "salario_bruto", "margem_disponivel")


def valor_json(valor: object) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return f"{valor:.2f}"
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def mudanca(campo: str, antes: object, depois: object, contexto: str | None = None) -> dict:
    return {
        "campo": campo,
        "rotulo": ROTULOS.get(campo, campo),
        "contexto": contexto,
        "antes": valor_json(antes),
        "depois": valor_json(depois),
    }


def comparar(campos: tuple[str, ...], antes: dict, depois: dict, contexto: str | None = None) -> list[dict]:
    return [
        mudanca(c, antes.get(c), depois[c], contexto)
        for c in campos
        if c in depois and valor_json(antes.get(c)) != valor_json(depois[c])
    ]


def registrar(sessao: Session, registros: list[dict]) -> None:
    if registros:
        sessao.execute(insert(AlteracaoCliente), registros)
