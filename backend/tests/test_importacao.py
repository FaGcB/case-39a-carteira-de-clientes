import pytest
from sqlalchemy import func, select

from app.importacao.processador import ImportacaoPerdida, processar, processar_proxima, reivindicar
from app.models import Cliente, Importacao, LinhaImportada, Vinculo
from tests.conftest import csv_bytes, linha_csv

ARQUIVO = csv_bytes(
    linha_csv(),
    linha_csv(
        cpf="17649590003",
        nome_cliente="Jose Carlos Ferreira",
        data_nascimento="1993-04-20",
        cnpj="22333888000117",
        razao_social="COOPERATIVA SANTA RITA",
        matricula="074158",
    ),
    linha_csv(cpf="12345678900"),
    linha_csv(
        cpf="17649590003",
        nome_cliente="J. C. Ferreira",
        data_nascimento="20/04/1993",
        cnpj="11444777000161",
        matricula="999",
    ),
    linha_csv(margem_disponivel="-1"),
    linha_csv(),
    linha_csv(cpf="17649590003", data_nascimento="1959-09-18"),
)


def enviar(api, conteudo=ARQUIVO, nome="carga.csv"):
    r = api.post("/api/importacoes", files={"arquivo": (nome, conteudo, "text/csv")})
    assert r.status_code == 202, r.text
    return r.json()


def rodar_worker(sessao):
    while processar_proxima(sessao, "teste"):
        pass


def test_post_responde_pendente_sem_processar(api):
    imp = enviar(api)
    assert imp["status"] == "PENDENTE"
    assert imp["processadas"] == 0


def test_importacao_completa(api, sessao):
    imp = enviar(api)
    rodar_worker(sessao)

    final = api.get(f"/api/importacoes/{imp['id']}").json()
    assert final["status"] == "CONCLUIDA"
    assert (final["total_linhas"], final["importadas"], final["invalidas"]) == (7, 4, 3)

    invalidas = api.get(f"/api/importacoes/{imp['id']}/linhas-invalidas").json()
    assert [item["linha"] for item in invalidas["items"]] == [4, 6, 8]
    assert "CPF com dígito verificador inválido" in invalidas["items"][0]["motivos"][0]
    assert "data de nascimento" in invalidas["items"][2]["motivos"][0]

    assert sessao.scalar(select(func.count(Cliente.id))) == 2
    assert sessao.scalar(select(func.count(Vinculo.id))) == 3
    assert sessao.scalar(select(func.count(LinhaImportada.id))) == 4
    jose = sessao.scalar(select(Cliente).where(Cliente.cpf == "17649590003"))
    assert jose.nome == "Jose Carlos Ferreira"
    assert jose.importacao_origem_id == imp["id"]


def test_reimportar_o_mesmo_arquivo_nao_duplica(api, sessao):
    enviar(api)
    rodar_worker(sessao)
    segunda = enviar(api)
    rodar_worker(sessao)

    assert sessao.scalar(select(func.count(Cliente.id))) == 2
    assert sessao.scalar(select(func.count(Vinculo.id))) == 3
    maria = sessao.scalar(select(Cliente).where(Cliente.cpf == "34603369000"))
    assert maria.ultima_importacao_id == segunda["id"]


def test_queda_no_meio_retoma_sem_duplicar(api, sessao):
    imp = enviar(api)
    assert reivindicar(sessao, "worker-a") == imp["id"]

    class Queda(Exception):
        pass

    def cair(_):
        raise Queda

    with pytest.raises(Queda):
        processar(sessao, imp["id"], "worker-a", tamanho_lote=3, apos_lote=cair)
    sessao.rollback()

    parcial = sessao.get(Importacao, imp["id"], populate_existing=True)
    assert (parcial.status, parcial.processadas, parcial.proxima_linha) == ("PROCESSANDO", 3, 3)

    assert reivindicar(sessao, "worker-b") is None
    sessao.execute(Importacao.__table__.update().values(heartbeat_em=func.now() - func.make_interval(0, 0, 0, 0, 1)))
    sessao.commit()
    assert reivindicar(sessao, "worker-b") == imp["id"]
    processar(sessao, imp["id"], "worker-b", tamanho_lote=3)

    final = sessao.get(Importacao, imp["id"], populate_existing=True)
    assert (final.status, final.importadas, final.invalidas, final.tentativas) == ("CONCLUIDA", 4, 3, 2)
    assert sessao.scalar(select(func.count(Cliente.id))) == 2
    assert sessao.scalar(select(func.count(Vinculo.id))) == 3


def test_worker_antigo_nao_continua_depois_de_perder_a_vez(api, sessao):
    imp = enviar(api)
    reivindicar(sessao, "worker-a")
    sessao.execute(Importacao.__table__.update().values(worker_id="worker-b"))
    sessao.commit()
    with pytest.raises(ImportacaoPerdida):
        processar(sessao, imp["id"], "worker-a")


def test_arquivo_sem_colunas_falha_com_mensagem(api, sessao):
    imp = enviar(api, b"nome;idade\nMaria;30\n")
    rodar_worker(sessao)
    final = api.get(f"/api/importacoes/{imp['id']}").json()
    assert final["status"] == "FALHOU"
    assert "colunas obrigatórias" in final["erro"]


def test_formato_nao_suportado(api):
    r = api.post("/api/importacoes", files={"arquivo": ("carga.pdf", b"%PDF", "application/pdf")})
    assert r.status_code == 422
    assert r.json()["erros"]["arquivo"]


def test_edicao_manual_vence_reimportacao(api, sessao):
    enviar(api)
    rodar_worker(sessao)
    maria = sessao.scalar(select(Cliente).where(Cliente.cpf == "34603369000"))
    ficha = api.get(f"/api/clientes/{maria.id}").json()
    corpo = {k: ficha[k] for k in ("nome", "data_nascimento", "sexo", "estado_civil", "email", "endereco")}
    corpo["telefone"] = "(11) 3333-4444"
    assert api.put(f"/api/clientes/{maria.id}", json=corpo).status_code == 200

    enviar(api)
    rodar_worker(sessao)
    assert api.get(f"/api/clientes/{maria.id}").json()["telefone"] == "1133334444"


def test_cliente_excluido_nao_volta_pela_importacao(api, sessao):
    enviar(api)
    rodar_worker(sessao)
    maria = sessao.scalar(select(Cliente).where(Cliente.cpf == "34603369000"))
    assert api.delete(f"/api/clientes/{maria.id}").status_code == 204

    imp = enviar(api, csv_bytes(linha_csv()))
    rodar_worker(sessao)
    assert api.get(f"/api/clientes/{maria.id}").status_code == 404
    motivos = api.get(f"/api/importacoes/{imp['id']}/linhas-invalidas").json()["items"][0]["motivos"]
    assert "excluído" in motivos[0]
