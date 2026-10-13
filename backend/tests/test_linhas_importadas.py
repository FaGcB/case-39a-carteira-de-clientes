from app.importacao.processador import processar_proxima
from tests.conftest import csv_bytes, linha_csv

OUTRA_EMPRESA = {"cnpj": "22333888000117", "razao_social": "SANTA RITA", "nome_fantasia": "Santa Rita"}
JOAO = {"cpf": "529.982.247-25", "nome_cliente": "JOAO PEREIRA", "email": "joao@exemplo.com.br", "matricula": "9"}


def importar(api, sessao, *linhas):
    r = api.post("/api/importacoes", files={"arquivo": ("carga.csv", csv_bytes(*linhas), "text/csv")})
    while processar_proxima(sessao, "teste"):
        pass
    return r.json()["id"]


def aceitas(api, imp, **params):
    r = api.get(f"/api/importacoes/{imp}/linhas-importadas", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_cada_linha_aceita_aparece_com_o_que_fez(api, sessao):
    imp = importar(
        api,
        sessao,
        linha_csv(),
        linha_csv(**OUTRA_EMPRESA, matricula="77"),
        linha_csv(cpf="123"),
        linha_csv(),
        linha_csv(**JOAO),
    )
    corpo = aceitas(api, imp)
    assert corpo["total"] == api.get(f"/api/importacoes/{imp}").json()["importadas"] == 4
    assert [(i["linha"], i["resultado"], i["cliente"]["nome"]) for i in corpo["items"]] == [
        (2, "NOVO_CLIENTE", "Maria Aparecida Souza"),
        (3, "NOVO_VINCULO", "Maria Aparecida Souza"),
        (5, "REPETIDA", "Maria Aparecida Souza"),
        (6, "NOVO_CLIENTE", "Joao Pereira"),
    ]
    primeira = corpo["items"][0]
    assert primeira["cliente"]["cpf"] == "34603369000"
    assert primeira["empresa"]["nome_fantasia"] == "Aurora Log"
    assert primeira["empresa"]["cnpj"] == "11444777000161"
    assert primeira["matricula"] == "538304"
    assert corpo["por_resultado"] == {"NOVO_CLIENTE": 2, "NOVO_VINCULO": 1, "REPETIDA": 1}


def test_segunda_importacao_separa_atualizadas_de_sem_mudanca(api, sessao):
    importar(api, sessao, linha_csv(), linha_csv(**OUTRA_EMPRESA, matricula="77"), linha_csv(**JOAO))
    imp = importar(
        api,
        sessao,
        linha_csv(margem_disponivel="300.00"),
        linha_csv(**OUTRA_EMPRESA, matricula="77"),
        linha_csv(**JOAO),
        linha_csv(**{**JOAO, "matricula": "10"}),
    )
    corpo = aceitas(api, imp)
    assert [i["resultado"] for i in corpo["items"]] == ["ATUALIZADA", "SEM_MUDANCA", "SEM_MUDANCA", "NOVO_VINCULO"]
    assert corpo["por_resultado"] == {"ATUALIZADA": 1, "SEM_MUDANCA": 2, "NOVO_VINCULO": 1}

    filtradas = aceitas(api, imp, resultado="SEM_MUDANCA")
    assert (filtradas["total"], [i["linha"] for i in filtradas["items"]]) == (2, [3, 4])
    assert filtradas["por_resultado"] == corpo["por_resultado"]


def test_mudanca_no_cadastro_marca_todas_as_linhas_do_cliente(api, sessao):
    importar(api, sessao, linha_csv(), linha_csv(**OUTRA_EMPRESA, matricula="77"))
    imp = importar(
        api,
        sessao,
        linha_csv(telefone="(11) 98888-7777"),
        linha_csv(**OUTRA_EMPRESA, matricula="77", telefone="(11) 98888-7777"),
    )
    assert [i["resultado"] for i in aceitas(api, imp)["items"]] == ["ATUALIZADA", "ATUALIZADA"]


def test_cliente_excluido_depois_continua_na_lista_marcado(api, sessao):
    imp = importar(api, sessao, linha_csv())
    cliente_id = aceitas(api, imp)["items"][0]["cliente"]["id"]
    assert api.delete(f"/api/clientes/{cliente_id}").status_code == 204
    assert aceitas(api, imp)["items"][0]["cliente"]["excluido"] is True


def test_paginacao_e_404(api, sessao):
    imp = importar(api, sessao, *(linha_csv(matricula=str(n)) for n in range(1, 26)))
    pagina2 = aceitas(api, imp, pagina=2, tamanho=20)
    assert (pagina2["total"], len(pagina2["items"]), pagina2["items"][0]["linha"]) == (25, 5, 22)
    assert api.get("/api/importacoes/999/linhas-importadas").status_code == 404
    assert api.get(f"/api/importacoes/{imp}/linhas-importadas", params={"resultado": "X"}).status_code == 422
