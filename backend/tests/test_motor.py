import random
from decimal import Decimal

from app.motor.gerador import PARCELAS, gerar_proposta
from app.motor.limitador import JanelaDeslizante


def test_mesmo_cpf_gera_sempre_a_mesma_proposta():
    a, b = gerar_proposta("34603369000"), gerar_proposta("34603369000")
    assert (a.valor, a.parcelas, a.taxa_mensal) == (b.valor, b.parcelas, b.taxa_mensal)


def test_valores_fixos_conferidos():
    p = gerar_proposta("34603369000")
    assert (p.valor, p.parcelas, p.taxa_mensal) == (Decimal("35300.00"), 72, Decimal("0.0300"))


def test_faixas_respeitadas_para_muitos_cpfs():
    aleatorio = random.Random(42)
    for _ in range(2000):
        p = gerar_proposta("".join(aleatorio.choice("0123456789") for _ in range(11)))
        assert Decimal(1000) <= p.valor <= Decimal(60000)
        assert p.valor % 100 == 0
        assert p.parcelas in PARCELAS
        assert Decimal("0.0149") <= p.taxa_mensal <= Decimal("0.0329")
        assert p.taxa_mensal == p.taxa_mensal.quantize(Decimal("0.0001"))


def test_cpfs_diferentes_geram_propostas_diferentes():
    propostas = {(p.valor, p.parcelas, p.taxa_mensal) for p in (gerar_proposta(f"{i:011d}") for i in range(200))}
    assert len(propostas) > 190


class Relogio:
    def __init__(self) -> None:
        self.agora = 1000.0

    def __call__(self) -> float:
        return self.agora


def test_janela_deslizante():
    relogio = Relogio()
    limitador = JanelaDeslizante(limite=10, janela=60, relogio=relogio)
    for i in range(10):
        relogio.agora = 1000 + i
        assert limitador.registrar("ip") is None
    relogio.agora = 1030
    assert limitador.registrar("ip") == 30
    relogio.agora = 1060
    assert limitador.registrar("ip") is None
    assert limitador.registrar("outro-ip") is None


def test_endpoint_responde_429_com_retry_after(api):
    for _ in range(10):
        assert api.get("/api/motor/proposta", params={"cpf": "346.033.690-00"}).status_code == 200
    r = api.get("/api/motor/proposta", params={"cpf": "34603369000"})
    assert r.status_code == 429
    assert 1 <= int(r.headers["Retry-After"]) <= 60
    assert "limite" in r.json()["mensagem"]


def test_endpoint_rejeita_cpf_invalido(api):
    r = api.get("/api/motor/proposta", params={"cpf": "12345678900"})
    assert r.status_code == 400
    assert "cpf" in r.json()["erros"]
