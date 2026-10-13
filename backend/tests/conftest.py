import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/carteira_teste"
)

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config as AlembicConfig  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.motor.rotas import get_limitador  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent

CABECALHO = (
    "cpf;nome_cliente;data_nascimento;sexo;estado_civil;email;telefone;cep_cliente;logradouro;numero;"
    "complemento;bairro;cidade_cliente;uf_cliente;cnpj;razao_social;nome_fantasia;setor;cep_empresa;"
    "cidade_empresa;uf_empresa;matricula;cargo;data_admissao;salario_bruto;margem_disponivel"
)


def linha_csv(**campos: str) -> str:
    base = {
        "cpf": "346.033.690-00",
        "nome_cliente": "MARIA APARECIDA SOUZA",
        "data_nascimento": "22/05/1993",
        "sexo": "F",
        "estado_civil": "Solteiro",
        "email": "maria@exemplo.com.br",
        "telefone": "(92) 91989-3816",
        "cep_cliente": "04553-401",
        "logradouro": "Avenida Brasil",
        "numero": "10",
        "complemento": "",
        "bairro": "Centro",
        "cidade_cliente": "Sao Paulo",
        "uf_cliente": "sp",
        "cnpj": "11.444.777/0001-61",
        "razao_social": "TRANSPORTES AURORA LTDA",
        "nome_fantasia": "Aurora Log",
        "setor": "Transporte",
        "cep_empresa": "04571010",
        "cidade_empresa": "Sao Paulo",
        "uf_empresa": "SP",
        "matricula": "538304",
        "cargo": "Almoxarife",
        "data_admissao": "2016-05-09",
        "salario_bruto": "R$ 4.519,96",
        "margem_disponivel": "427.47",
    }
    base.update(campos)
    return ";".join(base[c] for c in CABECALHO.split(";"))


def csv_bytes(*linhas: str) -> bytes:
    return ("\n".join([CABECALHO, *linhas]) + "\n").encode()


@pytest.fixture(scope="session", autouse=True)
def banco() -> Iterator[None]:
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    cfg = AlembicConfig(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def limpar() -> Iterator[None]:
    yield
    with engine.begin() as c:
        tabelas = (
            "linhas_importadas, alteracoes_cliente, vinculo_importacoes, vinculos, clientes, empresas, "
            "linhas_invalidas, importacoes"
        )
        c.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))
    get_limitador.cache_clear()


@pytest.fixture
def sessao() -> Iterator[Session]:
    with SessionLocal() as s:
        yield s


@pytest.fixture
def api() -> TestClient:
    return TestClient(app)
