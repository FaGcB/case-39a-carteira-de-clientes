from app.importacao.processador import processar_proxima
from tests.conftest import csv_bytes, linha_csv

CPF = "34603369000"


def importar(api, sessao, *linhas, nome="carga.csv"):
    r = api.post("/api/importacoes", files={"arquivo": (nome, csv_bytes(*linhas), "text/csv")})
    while processar_proxima(sessao, "teste"):
        pass
    return r.json()["id"]


def cliente_id(api):
    return api.get("/api/clientes", params={"documento": CPF}).json()["items"][0]["id"]


def historico(api):
    r = api.get(f"/api/clientes/{cliente_id(api)}/historico")
    assert r.status_code == 200, r.text
    return r.json()["items"]


def mudancas(entrada):
    return {(m["campo"], m["contexto"]): (m["antes"], m["depois"]) for m in entrada["mudancas"]}


def test_primeira_importacao_registra_a_criacao(api, sessao):
    imp = importar(api, sessao, linha_csv(), nome="janeiro.csv")
    [entrada] = historico(api)
    assert entrada["acao"] == "CRIACAO"
    assert entrada["importacao_id"] == imp
    assert entrada["descricao"] == f"Importação #{imp} (janeiro.csv)"


def test_reimportar_sem_mudanca_nao_gera_entrada(api, sessao):
    importar(api, sessao, linha_csv())
    importar(api, sessao, linha_csv())
    assert len(historico(api)) == 1


def test_segunda_importacao_guarda_valores_antigos(api, sessao):
    importar(api, sessao, linha_csv())
    segunda = importar(
        api,
        sessao,
        linha_csv(telefone="(11) 98888-7777", margem_disponivel="510.00"),
        linha_csv(
            telefone="(11) 98888-7777",
            cnpj="22333888000117",
            razao_social="SANTA RITA",
            nome_fantasia="Santa Rita",
            matricula="77",
        ),
    )
    recente, criacao = historico(api)
    assert criacao["acao"] == "CRIACAO"
    assert recente["acao"] == "ATUALIZACAO"
    assert recente["importacao_id"] == segunda
    assert mudancas(recente) == {
        ("telefone", None): ("92919893816", "11988887777"),
        ("margem_disponivel", "Aurora Log · matrícula 538304"): ("427.47", "510.00"),
        ("vinculo", None): (None, "Santa Rita · matrícula 77"),
    }


def test_campo_vazio_na_planilha_nao_vira_mudanca(api, sessao):
    importar(api, sessao, linha_csv())
    importar(api, sessao, linha_csv(telefone="", email=""))
    assert len(historico(api)) == 1


def test_edicao_manual_entra_no_historico(api, sessao):
    importar(api, sessao, linha_csv())
    ficha = api.get(f"/api/clientes/{cliente_id(api)}").json()
    corpo = {k: ficha[k] for k in ("nome", "data_nascimento", "sexo", "estado_civil", "email", "endereco")}
    corpo["telefone"] = "(11) 3333-4444"
    corpo["endereco"] = {**corpo["endereco"], "bairro": "Jardins"}
    assert api.put(f"/api/clientes/{ficha['id']}", json=corpo).status_code == 200

    recente = historico(api)[0]
    assert (recente["origem"], recente["descricao"]) == ("EDICAO", "Edição manual")
    assert mudancas(recente) == {
        ("telefone", None): ("92919893816", "1133334444"),
        ("bairro", None): ("Centro", "Jardins"),
    }

    importar(api, sessao, linha_csv(telefone="(92) 90000-0000", margem_disponivel="300.00"))
    assert list(mudancas(historico(api)[0])) == [("margem_disponivel", "Aurora Log · matrícula 538304")]


def test_historico_continua_depois_de_apagar_a_importacao(api, sessao):
    importar(api, sessao, linha_csv())
    segunda = importar(api, sessao, linha_csv(telefone="(11) 98888-7777"))
    assert api.delete(f"/api/importacoes/{segunda}").status_code == 200
    recente = historico(api)[0]
    assert recente["importacao_id"] is None
    assert recente["descricao"].startswith(f"Importação #{segunda}")


def test_historico_de_cliente_inexistente(api):
    assert api.get("/api/clientes/999/historico").status_code == 404
