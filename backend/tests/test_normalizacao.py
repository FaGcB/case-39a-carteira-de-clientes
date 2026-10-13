from datetime import date, datetime
from decimal import Decimal

import pytest

from app.importacao import normalizacao as n


@pytest.mark.parametrize("entrada", ["346.033.690-00", "34603369000", " 346033690-00 "])
def test_cpf_com_e_sem_mascara(entrada):
    assert n.normalizar_cpf(entrada) == "34603369000"


def test_cpf_numerico_do_excel_recupera_zero_a_esquerda():
    assert n.normalizar_cpf(2437434836) == "02437434836"


@pytest.mark.parametrize("invalido", ["12345678900", "11111111111", "3460336900", "abc"])
def test_cpf_invalido(invalido):
    with pytest.raises(n.ValorInvalido, match="CPF"):
        n.normalizar_cpf(invalido)


def test_cnpj():
    assert n.normalizar_cnpj("11.444.777/0001-61") == "11444777000161"
    with pytest.raises(n.ValorInvalido, match="CNPJ"):
        n.normalizar_cnpj("11222333000199")


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("1993-04-20", date(1993, 4, 20)),
        ("20/04/1993", date(1993, 4, 20)),
        ("1993-04-20 00:00:00", date(1993, 4, 20)),
        (datetime(1993, 4, 20, 0, 0), date(1993, 4, 20)),
        (34079, date(1993, 4, 20)),
    ],
)
def test_datas_em_formatos_mistos(entrada, esperado):
    assert n.normalizar_data(entrada, "Data") == esperado


@pytest.mark.parametrize("entrada", ["31/02/1980", "2023-13-01", "ontem"])
def test_data_inexistente(entrada):
    with pytest.raises(n.ValorInvalido):
        n.normalizar_data(entrada, "Data de nascimento")


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("R$ 4.519,96", Decimal("4519.96")),
        ("4519.96", Decimal("4519.96")),
        ("4.519,96", Decimal("4519.96")),
        ("4,519.96", Decimal("4519.96")),
        ("1.234.567", Decimal("1234567.00")),
        (4519.96, Decimal("4519.96")),
        (" 2400 ", Decimal("2400.00")),
    ],
)
def test_valores_monetarios(entrada, esperado):
    assert n.normalizar_valor(entrada, "Salário") == esperado


def test_valor_nao_numerico():
    with pytest.raises(n.ValorInvalido, match="não numérico"):
        n.normalizar_valor("a combinar", "Salário bruto")


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("  JOSE CARLOS DA SILVA ", "Jose Carlos da Silva"),
        ("wilson gomes de andrade", "Wilson Gomes de Andrade"),
        ("Sebastiao   Ribeiro  Neto", "Sebastiao Ribeiro Neto"),
    ],
)
def test_nome(entrada, esperado):
    assert n.normalizar_nome(entrada) == esperado


def test_nome_mais_completo_vence_abreviado():
    assert n.nome_mais_completo("J. C. Ferreira", "Jose Carlos Ferreira") == "Jose Carlos Ferreira"
    assert n.nome_mais_completo("Jose Carlos Ferreira", "J. C. Ferreira") == "Jose Carlos Ferreira"


def test_chave_de_busca_sem_acento():
    assert n.chave_busca("  José  Conceição ") == "jose conceicao"


def test_uf():
    assert n.normalizar_uf(" sp ", "UF") == "SP"
    with pytest.raises(n.ValorInvalido):
        n.normalizar_uf("XX", "UF")
