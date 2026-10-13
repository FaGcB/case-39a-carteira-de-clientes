from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.importacao import normalizacao as n
from app.importacao.leitura import LinhaBruta

IDADE_MINIMA_CLIENTE = 18
IDADE_MINIMA_ADMISSAO = 14


@dataclass(frozen=True)
class DadosCliente:
    cpf: str
    nome: str
    data_nascimento: date
    sexo: str | None
    estado_civil: str | None
    email: str | None
    telefone: str | None
    cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: str | None
    uf: str


@dataclass(frozen=True)
class DadosEmpresa:
    cnpj: str
    razao_social: str
    nome_fantasia: str
    setor: str
    cidade: str
    uf: str


@dataclass(frozen=True)
class DadosVinculo:
    matricula: str
    cargo: str
    data_admissao: date
    salario_bruto: Decimal
    margem_disponivel: Decimal


@dataclass(frozen=True)
class LinhaValida:
    numero: int
    cliente: DadosCliente
    empresa: DadosEmpresa
    vinculo: DadosVinculo


@dataclass(frozen=True)
class LinhaRejeitada:
    numero: int
    motivos: list[str]
    cpf: str | None
    nome: str | None


OBRIGATORIOS = {
    "cpf": "CPF",
    "nome_cliente": "Nome do cliente",
    "data_nascimento": "Data de nascimento",
    "cnpj": "CNPJ",
    "razao_social": "Razão social",
    "matricula": "Matrícula",
    "data_admissao": "Data de admissão",
    "salario_bruto": "Salário bruto",
    "margem_disponivel": "Margem disponível",
    "uf_cliente": "UF do cliente",
    "uf_empresa": "UF da empresa",
}


def validar_linha(linha: LinhaBruta, data_referencia: date) -> LinhaValida | LinhaRejeitada:
    v = linha.valores
    motivos: list[str] = []

    vazios = [campo for campo in OBRIGATORIOS if n.vazio(v.get(campo))]
    motivos.extend(f"Campo obrigatório vazio: {OBRIGATORIOS[campo]}" for campo in vazios)

    def tentar(campo: str, funcao, *args):
        if campo in vazios:
            return None
        try:
            return funcao(v.get(campo), *args)
        except n.ValorInvalido as e:
            motivos.append(str(e))
            return None

    cpf = tentar("cpf", n.normalizar_cpf)
    cnpj = tentar("cnpj", n.normalizar_cnpj)
    nascimento = tentar("data_nascimento", n.normalizar_data, "Data de nascimento")
    admissao = tentar("data_admissao", n.normalizar_data, "Data de admissão")
    salario = tentar("salario_bruto", n.normalizar_valor, "Salário bruto")
    margem = tentar("margem_disponivel", n.normalizar_valor, "Margem disponível")
    uf_cliente = tentar("uf_cliente", n.normalizar_uf, "UF do cliente")
    uf_empresa = tentar("uf_empresa", n.normalizar_uf, "UF da empresa")
    email = tentar("email", n.normalizar_email)

    if nascimento:
        if nascimento > data_referencia:
            motivos.append("Data de nascimento no futuro")
        elif n.idade_em(nascimento, data_referencia) < IDADE_MINIMA_CLIENTE:
            motivos.append(f"Cliente menor de {IDADE_MINIMA_CLIENTE} anos")
    if admissao and admissao > data_referencia:
        motivos.append("Data de admissão no futuro")
    if nascimento and admissao and n.idade_em(nascimento, admissao) < IDADE_MINIMA_ADMISSAO:
        motivos.append(f"Admissão antes dos {IDADE_MINIMA_ADMISSAO} anos de idade")

    if salario is not None and salario < 0:
        motivos.append("Salário bruto negativo")
    if margem is not None:
        if margem < 0:
            motivos.append("Margem disponível negativa")
        elif salario is not None and margem > salario:
            motivos.append("Margem disponível maior que o salário bruto")

    nome = n.normalizar_nome(v.get("nome_cliente")) if "nome_cliente" not in vazios else None

    if motivos:
        return LinhaRejeitada(
            numero=linha.numero,
            motivos=motivos,
            cpf=n.texto(v.get("cpf")) or None,
            nome=n.texto(v.get("nome_cliente")) or None,
        )

    assert cpf and cnpj and nascimento and admissao and nome and uf_cliente and uf_empresa
    assert salario is not None and margem is not None
    return LinhaValida(
        numero=linha.numero,
        cliente=DadosCliente(
            cpf=cpf,
            nome=nome,
            data_nascimento=nascimento,
            sexo=n.normalizar_sexo(v.get("sexo")),
            estado_civil=n.texto(v.get("estado_civil")) or None,
            email=email,
            telefone=n.normalizar_telefone(v.get("telefone")),
            cep=n.normalizar_cep(v.get("cep_cliente")),
            logradouro=n.texto(v.get("logradouro")) or None,
            numero=n.texto(v.get("numero")) or None,
            complemento=n.texto(v.get("complemento")) or None,
            bairro=n.texto(v.get("bairro")) or None,
            cidade=n.texto(v.get("cidade_cliente")) or None,
            uf=uf_cliente,
        ),
        empresa=DadosEmpresa(
            cnpj=cnpj,
            razao_social=n.texto(v.get("razao_social")),
            nome_fantasia=n.texto(v.get("nome_fantasia")) or n.texto(v.get("razao_social")),
            setor=n.texto(v.get("setor")),
            cidade=n.texto(v.get("cidade_empresa")),
            uf=uf_empresa,
        ),
        vinculo=DadosVinculo(
            matricula=n.texto(v.get("matricula")),
            cargo=n.texto(v.get("cargo")),
            data_admissao=admissao,
            salario_bruto=salario,
            margem_disponivel=margem,
        ),
    )
