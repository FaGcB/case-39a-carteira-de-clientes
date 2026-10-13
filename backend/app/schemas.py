import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.importacao.normalizacao import UFS, idade_em, somente_digitos


class Paginado[T](BaseModel):
    items: list[T]
    total: int
    pagina: int
    tamanho: int


StatusImportacao = Literal["PENDENTE", "PROCESSANDO", "CONCLUIDA", "FALHOU"]


class ImportacaoOut(BaseModel):
    id: int
    arquivo: str
    status: StatusImportacao
    total_linhas: int | None
    processadas: int
    importadas: int
    invalidas: int
    criada_em: datetime
    finalizada_em: datetime | None
    erro: str | None


class LinhaInvalidaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    linha: int
    motivos: list[str]
    cpf: str | None
    nome: str | None


ResultadoLinha = Literal["NOVO_CLIENTE", "NOVO_VINCULO", "ATUALIZADA", "SEM_MUDANCA", "REPETIDA"]


class ClienteDaLinha(BaseModel):
    id: int
    nome: str
    cpf: str
    excluido: bool


class EmpresaDaLinha(BaseModel):
    id: int
    nome_fantasia: str
    cnpj: str


class LinhaImportadaOut(BaseModel):
    linha: int | None
    resultado: ResultadoLinha | None
    cliente: ClienteDaLinha
    empresa: EmpresaDaLinha
    matricula: str


class LinhasImportadasOut(Paginado[LinhaImportadaOut]):
    por_resultado: dict[str, int]


class EmpresaRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cnpj: str
    razao_social: str
    nome_fantasia: str


class EmpresaOut(EmpresaRef):
    setor: str
    cidade: str
    uf: str
    total_vinculos: int
    margem_total: float


class ClienteRef(BaseModel):
    id: int
    nome: str
    cpf: str


class VinculoDaEmpresaOut(BaseModel):
    id: int
    cliente: ClienteRef
    matricula: str
    cargo: str
    data_admissao: date
    salario_bruto: float
    margem_disponivel: float


class ClienteResumo(BaseModel):
    id: int
    nome: str
    cpf: str
    empresas: list[EmpresaRef]
    margem_disponivel: float
    ultima_importacao_em: datetime | None


class Endereco(BaseModel):
    cep: str
    logradouro: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    uf: str


class VinculoOut(BaseModel):
    id: int
    empresa: EmpresaRef
    matricula: str
    cargo: str
    data_admissao: date
    salario_bruto: float
    margem_disponivel: float
    importacao_id: int | None


class ClienteOut(BaseModel):
    id: int
    cpf: str
    nome: str
    data_nascimento: date
    sexo: Literal["F", "M"] | None
    estado_civil: str | None
    email: str | None
    telefone: str | None
    endereco: Endereco
    vinculos: list[VinculoOut]
    criado_em: datetime
    atualizado_em: datetime
    ultima_importacao_id: int | None


def _obrigatorio(v: str | None, mensagem: str) -> str:
    v = re.sub(r"\s+", " ", v or "").strip()
    if not v:
        raise ValueError(mensagem)
    return v


class EnderecoIn(BaseModel):
    cep: str
    logradouro: str
    numero: str
    complemento: str | None = None
    bairro: str
    cidade: str
    uf: str

    @field_validator("cep")
    @classmethod
    def _cep(cls, v: str) -> str:
        d = somente_digitos(v)
        if len(d) != 8:
            raise ValueError("CEP precisa ter 8 dígitos.")
        return d

    @field_validator("logradouro")
    @classmethod
    def _logradouro(cls, v: str) -> str:
        return _obrigatorio(v, "Informe o logradouro.")

    @field_validator("numero")
    @classmethod
    def _numero(cls, v: str) -> str:
        return _obrigatorio(v, "Informe o número.")

    @field_validator("bairro")
    @classmethod
    def _bairro(cls, v: str) -> str:
        return _obrigatorio(v, "Informe o bairro.")

    @field_validator("cidade")
    @classmethod
    def _cidade(cls, v: str) -> str:
        return _obrigatorio(v, "Informe a cidade.")

    @field_validator("uf")
    @classmethod
    def _uf(cls, v: str) -> str:
        uf = (v or "").strip().upper()
        if uf not in UFS:
            raise ValueError("UF inexistente.")
        return uf

    @field_validator("complemento")
    @classmethod
    def _complemento(cls, v: str | None) -> str | None:
        return (v or "").strip() or None


class ClienteIn(BaseModel):
    nome: str
    data_nascimento: date
    sexo: Literal["F", "M"] | None = None
    estado_civil: str | None = None
    email: str | None = None
    telefone: str | None = None
    endereco: EnderecoIn

    @field_validator("nome")
    @classmethod
    def _nome(cls, v: str) -> str:
        nome = _obrigatorio(v, "Informe o nome completo.")
        if len(nome) < 3:
            raise ValueError("Informe o nome completo.")
        if len(nome) > 150:
            raise ValueError("Use no máximo 150 caracteres.")
        return nome

    @field_validator("data_nascimento")
    @classmethod
    def _nascimento(cls, v: date) -> date:
        hoje = date.today()
        if v > hoje:
            raise ValueError("A data de nascimento não pode estar no futuro.")
        if idade_em(v, hoje) < 18:
            raise ValueError("O cliente precisa ter pelo menos 18 anos.")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str | None) -> str | None:
        email = (v or "").strip().lower()
        if not email:
            return None
        if not re.fullmatch(r"[^@\s]+@[^@\s.]+(\.[^@\s.]+)+", email) or ".." in email:
            raise ValueError("E-mail em formato inválido.")
        return email

    @field_validator("telefone")
    @classmethod
    def _telefone(cls, v: str | None) -> str | None:
        d = somente_digitos(v or "")
        if not d:
            return None
        if len(d) not in (10, 11):
            raise ValueError("Telefone precisa ter DDD + 8 ou 9 dígitos.")
        return d

    @field_validator("estado_civil")
    @classmethod
    def _estado_civil(cls, v: str | None) -> str | None:
        return (v or "").strip()[:30] or None


class EmpresaIn(BaseModel):
    razao_social: str
    nome_fantasia: str
    setor: str

    @field_validator("razao_social")
    @classmethod
    def _razao(cls, v: str) -> str:
        r = _obrigatorio(v, "Informe a razão social.")
        if len(r) > 150:
            raise ValueError("Use no máximo 150 caracteres.")
        return r

    @field_validator("nome_fantasia")
    @classmethod
    def _fantasia(cls, v: str) -> str:
        r = _obrigatorio(v, "Informe o nome fantasia.")
        if len(r) > 150:
            raise ValueError("Use no máximo 150 caracteres.")
        return r

    @field_validator("setor")
    @classmethod
    def _setor(cls, v: str) -> str:
        r = _obrigatorio(v, "Informe o setor.")
        if len(r) > 100:
            raise ValueError("Use no máximo 100 caracteres.")
        return r


class PropostaOut(BaseModel):
    cpf: str
    valor: float
    parcelas: int
    taxa_mensal: float
    gerado_em: datetime


class VinculosPorEmpresa(BaseModel):
    empresa: EmpresaRef
    total: int


class ResumoOut(BaseModel):
    clientes: int
    empresas: int
    vinculos: int
    importacoes: int
    linhas_invalidas: int
    ultima_importacao: ImportacaoOut | None
    vinculos_por_empresa: list[VinculosPorEmpresa]


class ExclusaoImportacaoOut(BaseModel):
    importacao_id: int
    arquivo: str
    vinculos_removidos: int
    clientes_removidos: int
    clientes_mantidos: int
    empresas_removidas: int
    linhas_rejeitadas_removidas: int


class MudancaOut(BaseModel):
    campo: str
    rotulo: str
    contexto: str | None = None
    antes: str | None
    depois: str | None


class AlteracaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origem: Literal["IMPORTACAO", "EDICAO"]
    acao: Literal["CRIACAO", "ATUALIZACAO"]
    importacao_id: int | None
    descricao: str
    mudancas: list[MudancaOut]
    criado_em: datetime
