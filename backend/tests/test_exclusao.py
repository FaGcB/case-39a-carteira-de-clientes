import pytest
from sqlalchemy import func, select

from app.importacao.processador import processar_proxima
from app.models import Cliente, Empresa, Importacao, Vinculo
from tests.conftest import csv_bytes, linha_csv

MARIA = {"cpf": "34603369000", "nome_cliente": "Maria Aparecida Souza"}
JOSE = {
    "cpf": "17649590003",
    "nome_cliente": "Jose Carlos Ferreira",
    "data_nascimento": "1993-04-20",
    "cnpj": "22333888000117",
    "razao_social": "COOPERATIVA SANTA RITA",
    "nome_fantasia": "Santa Rita",
    "matricula": "074158",
}
ANA = {
    "cpf": "43167816007",
    "nome_cliente": "Ana Lucia Batista",
    "data_nascimento": "1953-12-24",
    "cnpj": "33222999000172",
    "razao_social": "METALURGICA VALE VERDE",
    "nome_fantasia": "Vale Verde",
    "matricula": "677657",
}


def importar(api, sessao, *linhas):
    r = api.post("/api/importacoes", files={"arquivo": ("carga.csv", csv_bytes(*linhas), "text/csv")})
    while processar_proxima(sessao, "teste"):
        pass
    return r.json()["id"]


def contar(sessao, modelo):
    return sessao.scalar(select(func.count()).select_from(modelo))


@pytest.fixture
def duas_importacoes(api, sessao):
    primeira = importar(api, sessao, linha_csv(**MARIA), linha_csv(**JOSE), linha_csv(cpf="12345678900"))
    segunda = importar(api, sessao, linha_csv(**MARIA, telefone="(11) 98888-7777"), linha_csv(**ANA))
    return primeira, segunda


def test_previa_mostra_o_que_sai_sem_apagar(api, sessao, duas_importacoes):
    _, segunda = duas_importacoes
    r = api.get(f"/api/importacoes/{segunda}/exclusao")
    assert r.status_code == 200
    assert r.json() == {
        "importacao_id": segunda,
        "arquivo": "carga.csv",
        "vinculos_removidos": 1,
        "clientes_removidos": 1,
        "clientes_mantidos": 1,
        "empresas_removidas": 1,
        "linhas_rejeitadas_removidas": 0,
    }
    assert (contar(sessao, Cliente), contar(sessao, Vinculo), contar(sessao, Importacao)) == (3, 3, 2)


def test_apagar_a_ultima_mantem_quem_veio_antes(api, sessao, duas_importacoes):
    primeira, segunda = duas_importacoes
    r = api.delete(f"/api/importacoes/{segunda}")
    assert r.status_code == 200, r.text

    nomes = [c["nome"] for c in api.get("/api/clientes").json()["items"]]
    assert nomes == ["Jose Carlos Ferreira", "Maria Aparecida Souza"]
    assert api.get(f"/api/importacoes/{segunda}").status_code == 404
    assert contar(sessao, Empresa) == 2

    maria = sessao.scalar(select(Cliente).where(Cliente.cpf == MARIA["cpf"]))
    assert (maria.importacao_origem_id, maria.ultima_importacao_id) == (primeira, primeira)
    assert maria.telefone == "11988887777"


def test_apagar_a_primeira_mantem_quem_tambem_esta_na_segunda(api, sessao, duas_importacoes):
    primeira, segunda = duas_importacoes
    r = api.delete(f"/api/importacoes/{primeira}")
    assert r.json()["clientes_removidos"] == 1
    assert r.json()["linhas_rejeitadas_removidas"] == 1

    nomes = [c["nome"] for c in api.get("/api/clientes").json()["items"]]
    assert nomes == ["Ana Lucia Batista", "Maria Aparecida Souza"]
    maria = sessao.scalar(select(Cliente).where(Cliente.cpf == MARIA["cpf"]))
    assert (maria.importacao_origem_id, maria.ultima_importacao_id) == (segunda, segunda)
    santa_rita = sessao.scalar(select(Empresa).where(Empresa.cnpj == "22333888000117"))
    assert santa_rita is None


def test_apagar_as_duas_zera_a_base(api, sessao, duas_importacoes):
    for importacao_id in duas_importacoes:
        assert api.delete(f"/api/importacoes/{importacao_id}").status_code == 200
    assert (contar(sessao, Cliente), contar(sessao, Empresa), contar(sessao, Vinculo)) == (0, 0, 0)


def test_reimportar_depois_de_apagar(api, sessao, duas_importacoes):
    _, segunda = duas_importacoes
    api.delete(f"/api/importacoes/{segunda}")
    importar(api, sessao, linha_csv(**ANA))
    assert api.get("/api/clientes", params={"nome": "ana"}).json()["total"] == 1


def test_nao_apaga_importacao_em_andamento(api):
    r = api.post("/api/importacoes", files={"arquivo": ("c.csv", csv_bytes(linha_csv()), "text/csv")})
    resposta = api.delete(f"/api/importacoes/{r.json()['id']}")
    assert resposta.status_code == 409
    assert "andamento" in resposta.json()["mensagem"]


def test_importacao_inexistente(api):
    assert api.delete("/api/importacoes/999").status_code == 404
    assert api.get("/api/importacoes/999/exclusao").status_code == 404
