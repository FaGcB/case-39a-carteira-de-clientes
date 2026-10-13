from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, deferred, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Importacao(Base):
    __tablename__ = "importacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    arquivo_nome: Mapped[str] = mapped_column(String(255))
    arquivo_hash: Mapped[str] = mapped_column(String(64))
    conteudo: Mapped[bytes] = deferred(mapped_column(LargeBinary))
    status: Mapped[str] = mapped_column(String(12), default="PENDENTE")
    total_linhas: Mapped[int | None] = mapped_column(Integer)
    processadas: Mapped[int] = mapped_column(Integer, default=0)
    importadas: Mapped[int] = mapped_column(Integer, default=0)
    invalidas: Mapped[int] = mapped_column(Integer, default=0)
    proxima_linha: Mapped[int] = mapped_column(Integer, default=0)
    tentativas: Mapped[int] = mapped_column(Integer, default=0)
    erro: Mapped[str | None] = mapped_column(Text)
    worker_id: Mapped[str | None] = mapped_column(String(64))
    heartbeat_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    iniciada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LinhaInvalida(Base):
    __tablename__ = "linhas_invalidas"

    id: Mapped[int] = mapped_column(primary_key=True)
    importacao_id: Mapped[int] = mapped_column(ForeignKey("importacoes.id", ondelete="CASCADE"))
    linha: Mapped[int] = mapped_column(Integer)
    motivos: Mapped[list[str]] = mapped_column(ARRAY(Text))
    cpf: Mapped[str | None] = mapped_column(String(32))
    nome: Mapped[str | None] = mapped_column(String(255))


class LinhaImportada(Base):
    __tablename__ = "linhas_importadas"

    id: Mapped[int] = mapped_column(primary_key=True)
    importacao_id: Mapped[int] = mapped_column(ForeignKey("importacoes.id", ondelete="CASCADE"))
    linha: Mapped[int | None] = mapped_column(Integer)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"))
    vinculo_id: Mapped[int] = mapped_column(ForeignKey("vinculos.id", ondelete="CASCADE"))
    resultado: Mapped[str | None] = mapped_column(String(14))


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True)
    razao_social: Mapped[str] = mapped_column(String(150))
    nome_fantasia: Mapped[str] = mapped_column(String(150))
    setor: Mapped[str] = mapped_column(String(100))
    cidade: Mapped[str] = mapped_column(String(100))
    uf: Mapped[str] = mapped_column(String(2))
    importacao_origem_id: Mapped[int | None] = mapped_column(ForeignKey("importacoes.id"))
    ultima_importacao_id: Mapped[int | None] = mapped_column(ForeignKey("importacoes.id"))
    editado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True)
    nome: Mapped[str] = mapped_column(String(150))
    nome_busca: Mapped[str] = mapped_column(String(150))
    data_nascimento: Mapped[date] = mapped_column(Date)
    sexo: Mapped[str | None] = mapped_column(String(1))
    estado_civil: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))
    telefone: Mapped[str | None] = mapped_column(String(11))
    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(150))
    numero: Mapped[str | None] = mapped_column(String(20))
    complemento: Mapped[str | None] = mapped_column(String(100))
    bairro: Mapped[str | None] = mapped_column(String(100))
    cidade: Mapped[str | None] = mapped_column(String(100))
    uf: Mapped[str | None] = mapped_column(String(2))
    importacao_origem_id: Mapped[int | None] = mapped_column(ForeignKey("importacoes.id"))
    ultima_importacao_id: Mapped[int | None] = mapped_column(ForeignKey("importacoes.id"))
    ultima_importacao_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    editado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vinculos: Mapped[list["Vinculo"]] = relationship(back_populates="cliente", order_by="Vinculo.data_admissao")


class Vinculo(Base):
    __tablename__ = "vinculos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"))
    matricula: Mapped[str] = mapped_column(String(30))
    cargo: Mapped[str] = mapped_column(String(100))
    data_admissao: Mapped[date] = mapped_column(Date)
    salario_bruto: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    margem_disponivel: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    importacao_origem_id: Mapped[int | None] = mapped_column(ForeignKey("importacoes.id"))
    ultima_importacao_id: Mapped[int | None] = mapped_column(ForeignKey("importacoes.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cliente: Mapped[Cliente] = relationship(back_populates="vinculos")
    empresa: Mapped[Empresa] = relationship()


vinculo_importacoes = Table(
    "vinculo_importacoes",
    Base.metadata,
    Column("importacao_id", BigInteger, ForeignKey("importacoes.id", ondelete="CASCADE"), primary_key=True),
    Column("vinculo_id", BigInteger, ForeignKey("vinculos.id", ondelete="CASCADE"), primary_key=True),
)


class AlteracaoCliente(Base):
    __tablename__ = "alteracoes_cliente"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"))
    origem: Mapped[str] = mapped_column(String(10))
    acao: Mapped[str] = mapped_column(String(12))
    importacao_id: Mapped[int | None] = mapped_column(ForeignKey("importacoes.id", ondelete="SET NULL"))
    descricao: Mapped[str] = mapped_column(String(300))
    mudancas: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
