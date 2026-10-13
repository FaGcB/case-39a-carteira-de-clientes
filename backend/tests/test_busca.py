import pytest

from app.importacao.processador import processar_proxima
from tests.conftest import csv_bytes, linha_csv


@pytest.fixture
def base(api, sessao):
    arquivo = csv_bytes(
        linha_csv(cpf="34603369000", nome_cliente="José Carlos Ferreira"),
        linha_csv(cpf="17649590003", nome_cliente="Maria José da Silva", matricula="2"),
        linha_csv(
            cpf="43167816007",
            nome_cliente="Ana Lucia Batista",
            cnpj="33222999000172",
            razao_social="METALURGICA VALE VERDE",
            nome_fantasia="Vale Verde",
            matricula="3",
        ),
        linha_csv(
            cpf="43167816007",
            nome_cliente="Ana Lucia Batista",
            cnpj="11444777000161",
            matricula="4",
            margem_disponivel="100.00",
        ),
    )
    api.post("/api/importacoes", files={"arquivo": ("c.csv", arquivo, "text/csv")})
    while processar_proxima(sessao, "teste"):
        pass


def nomes(api, **params):
    r = api.get("/api/clientes", params=params)
    assert r.status_code == 200, r.text
    return [c["nome"] for c in r.json()["items"]], r.json()["total"]


def test_nome_parcial_sem_acento_nem_caixa(api, base):
    assert nomes(api, nome="jose") == (["José Carlos Ferreira", "Maria José da Silva"], 2)
    assert nomes(api, nome="JOSÉ ferreira") == (["José Carlos Ferreira"], 1)
    assert nomes(api, nome="lucia") == (["Ana Lucia Batista"], 1)


def test_documento_com_e_sem_mascara(api, base):
    assert nomes(api, documento="346.033.690-00") == (["José Carlos Ferreira"], 1)
    assert nomes(api, documento="34603369000") == (["José Carlos Ferreira"], 1)
    assert nomes(api, documento="346.033") == (["José Carlos Ferreira"], 1)


def test_cnpj_traz_clientes_da_empresa(api, base):
    assert nomes(api, documento="11.444.777/0001-61")[1] == 3
    assert nomes(api, documento="33222999000172") == (["Ana Lucia Batista"], 1)


def test_filtros_combinados(api, base):
    assert nomes(api, nome="maria", documento="11444777000161") == (["Maria José da Silva"], 1)
    assert nomes(api, nome="maria", documento="33222999000172") == ([], 0)


def test_ordenacao_e_paginacao(api, base):
    assert nomes(api, ordem="nome", direcao="desc")[0][0] == "Maria José da Silva"
    pagina1, total = nomes(api, tamanho=2, pagina=1)
    pagina2, _ = nomes(api, tamanho=2, pagina=2)
    assert total == 3
    assert len(pagina1) == 2 and len(pagina2) == 1
    assert not set(pagina1) & set(pagina2)


def test_cliente_com_dois_vinculos_aparece_uma_vez_com_margem_somada(api, base):
    item = api.get("/api/clientes", params={"nome": "ana"}).json()["items"][0]
    assert len(item["empresas"]) == 2
    assert item["margem_disponivel"] == pytest.approx(427.47 + 100.00)


def test_parametro_invalido_volta_422_no_formato_da_api(api, base):
    r = api.get("/api/clientes", params={"ordem": "salario"})
    assert r.status_code == 422
    assert "ordem" in r.json()["erros"]


def test_ficha_da_empresa_lista_os_clientes_vinculados(api, base):
    aurora = api.get("/api/empresas", params={"busca": "11444777000161"}).json()["items"][0]
    assert aurora["total_vinculos"] == 3
    assert aurora["margem_total"] == pytest.approx(427.47 * 2 + 100.00)

    r = api.get(f"/api/empresas/{aurora['id']}/vinculos").json()
    assert r["total"] == 3
    assert [v["cliente"]["nome"] for v in r["items"]] == [
        "Ana Lucia Batista",
        "José Carlos Ferreira",
        "Maria José da Silva",
    ]
    assert r["items"][0]["matricula"] == "4"
    filtrado = api.get(f"/api/empresas/{aurora['id']}/vinculos", params={"nome": "jose"}).json()
    assert filtrado["total"] == 2


def test_ficha_de_empresa_inexistente(api, base):
    assert api.get("/api/empresas/999/vinculos").status_code == 404
