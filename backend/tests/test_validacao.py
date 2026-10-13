from datetime import date

from app.importacao.leitura import LinhaBruta, ler_planilha
from app.importacao.validacao import LinhaRejeitada, LinhaValida, validar_linha
from tests.conftest import RAIZ, csv_bytes, linha_csv

HOJE = date(2026, 10, 10)


def validar(**campos):
    linhas = ler_planilha("t.csv", csv_bytes(linha_csv(**campos)))
    return validar_linha(linhas[0], HOJE)


def test_linha_valida_sai_normalizada():
    r = validar()
    assert isinstance(r, LinhaValida)
    assert r.cliente.cpf == "34603369000"
    assert r.cliente.nome == "Maria Aparecida Souza"
    assert r.cliente.uf == "SP"
    assert r.cliente.telefone == "92919893816"
    assert r.empresa.cnpj == "11444777000161"
    assert str(r.vinculo.salario_bruto) == "4519.96"


def test_todos_os_motivos_aparecem_juntos():
    r = validar(cpf="123.456.789-00", data_nascimento="31/02/1980", salario_bruto="a combinar")
    assert isinstance(r, LinhaRejeitada)
    assert len(r.motivos) == 3


def test_margem_inconsistente():
    assert "Margem disponível negativa" in validar(margem_disponivel="-120.00").motivos
    assert (
        "Margem disponível maior que o salário bruto"
        in validar(salario_bruto="2400.00", margem_disponivel="3100.00").motivos
    )


def test_menor_de_idade_na_data_da_importacao():
    assert "Cliente menor de 18 anos" in validar(data_nascimento="2008-10-11", data_admissao="2026-01-02").motivos
    assert isinstance(validar(data_nascimento="2008-10-10", data_admissao="2026-01-02"), LinhaValida)


def test_campos_obrigatorios_vazios():
    r = validar(nome_cliente="  ", matricula="")
    assert "Campo obrigatório vazio: Nome do cliente" in r.motivos
    assert "Campo obrigatório vazio: Matrícula" in r.motivos


def test_admissao_antes_dos_14_anos():
    r = validar(data_nascimento="1998-03-27", data_admissao="2008-06-25")
    assert "Admissão antes dos 14 anos de idade" in r.motivos


def test_arquivo_de_exemplo_csv_e_xlsx_dao_o_mesmo_resultado():
    resultados = {}
    for nome in ("exemplo-carga-clientes.csv", "exemplo-carga-clientes.xlsx"):
        caminho = RAIZ / "exemplos" / nome
        linhas = ler_planilha(nome, caminho.read_bytes())
        rejeitadas = [item.numero for item in linhas if isinstance(validar_linha(item, HOJE), LinhaRejeitada)]
        resultados[nome] = (len(linhas), rejeitadas)
    csv, xlsx = resultados.values()
    assert csv == xlsx
    assert csv[0] == 116
    assert csv[1] == [30, 59, 86, 98, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117]


def test_xlsx_com_celulas_tipadas():
    from datetime import datetime

    bruta = LinhaBruta(
        2,
        {
            "cpf": 2437434836,
            "nome_cliente": "Fatima Regina Bezerra",
            "data_nascimento": datetime(1964, 5, 21),
            "data_admissao": 44624,
            "salario_bruto": 3469.51,
            "margem_disponivel": 797.13,
            "cnpj": 11444777000161,
            "razao_social": "X",
            "matricula": 636200.0,
            "uf_cliente": "SP",
            "uf_empresa": "SP",
        },
    )
    r = validar_linha(bruta, HOJE)
    assert isinstance(r, LinhaValida), getattr(r, "motivos", None)
    assert r.cliente.cpf == "02437434836"
    assert r.vinculo.data_admissao == date(2022, 3, 4)
    assert r.vinculo.matricula == "636200"
