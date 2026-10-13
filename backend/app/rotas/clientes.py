from collections import defaultdict
from typing import Literal

from fastapi import APIRouter, Query, Response
from sqlalchemy import Select, and_, exists, func, select
from sqlalchemy.orm import Session, selectinload

from app import historico
from app.db import Db
from app.erros import ErroApi
from app.importacao.normalizacao import chave_busca, somente_digitos
from app.models import AlteracaoCliente, Cliente, Empresa, Vinculo
from app.schemas import (
    AlteracaoOut,
    ClienteIn,
    ClienteOut,
    ClienteResumo,
    EmpresaRef,
    Endereco,
    Paginado,
    VinculoOut,
)

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


def aplicar_filtros(consulta: Select, nome: str | None, documento: str | None) -> Select:
    consulta = consulta.where(Cliente.excluido_em.is_(None))
    if nome:
        for termo in chave_busca(nome).split(" "):
            escapado = termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            consulta = consulta.where(Cliente.nome_busca.like(f"%{escapado}%"))
    digitos = somente_digitos(documento or "")
    if digitos:
        if len(digitos) == 14:
            consulta = consulta.where(
                exists().where(
                    and_(Vinculo.cliente_id == Cliente.id, Vinculo.empresa_id == Empresa.id, Empresa.cnpj == digitos)
                )
            )
        elif len(digitos) > 11:
            consulta = consulta.where(
                exists().where(
                    and_(
                        Vinculo.cliente_id == Cliente.id,
                        Vinculo.empresa_id == Empresa.id,
                        Empresa.cnpj.like(f"{digitos}%"),
                    )
                )
            )
        else:
            consulta = consulta.where(Cliente.cpf.like(f"{digitos}%"))
    return consulta


@router.get("", response_model=Paginado[ClienteResumo])
def listar(
    db: Db,
    nome: str | None = Query(None, max_length=150),
    documento: str | None = Query(None, max_length=30),
    ordem: Literal["nome", "importacao"] = "nome",
    direcao: Literal["asc", "desc"] = "asc",
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
) -> Paginado[ClienteResumo]:
    total = db.scalar(aplicar_filtros(select(func.count(Cliente.id)), nome, documento)) or 0

    coluna = Cliente.nome_busca if ordem == "nome" else Cliente.ultima_importacao_em
    ordenacao = [coluna.asc(), Cliente.id.asc()] if direcao == "asc" else [coluna.desc(), Cliente.id.desc()]
    clientes = db.execute(
        aplicar_filtros(select(Cliente.id, Cliente.nome, Cliente.cpf, Cliente.ultima_importacao_em), nome, documento)
        .order_by(*ordenacao)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()

    ids = [c.id for c in clientes]
    empresas: dict[int, dict[int, EmpresaRef]] = defaultdict(dict)
    margens: dict[int, float] = defaultdict(float)
    if ids:
        for v, e in db.execute(
            select(Vinculo, Empresa)
            .join(Empresa, Empresa.id == Vinculo.empresa_id)
            .where(Vinculo.cliente_id.in_(ids))
            .order_by(Vinculo.data_admissao)
        ):
            empresas[v.cliente_id].setdefault(e.id, EmpresaRef.model_validate(e))
            margens[v.cliente_id] += float(v.margem_disponivel)

    itens = [
        ClienteResumo(
            id=c.id,
            nome=c.nome,
            cpf=c.cpf,
            empresas=list(empresas[c.id].values()),
            margem_disponivel=round(margens[c.id], 2),
            ultima_importacao_em=c.ultima_importacao_em,
        )
        for c in clientes
    ]
    return Paginado(items=itens, total=total, pagina=pagina, tamanho=tamanho)


def _carregar(db: Session, cliente_id: int) -> Cliente:
    cliente = db.scalar(
        select(Cliente)
        .options(selectinload(Cliente.vinculos).selectinload(Vinculo.empresa))
        .where(Cliente.id == cliente_id, Cliente.excluido_em.is_(None))
        .execution_options(populate_existing=True)
    )
    if cliente is None:
        raise ErroApi(404, "Cliente não encontrado. Ele pode ter sido excluído.")
    return cliente


def cliente_out(c: Cliente) -> ClienteOut:
    return ClienteOut(
        id=c.id,
        cpf=c.cpf,
        nome=c.nome,
        data_nascimento=c.data_nascimento,
        sexo=c.sexo,
        estado_civil=c.estado_civil,
        email=c.email,
        telefone=c.telefone,
        endereco=Endereco(
            cep=c.cep or "",
            logradouro=c.logradouro or "",
            numero=c.numero or "",
            complemento=c.complemento,
            bairro=c.bairro or "",
            cidade=c.cidade or "",
            uf=c.uf or "",
        ),
        vinculos=[
            VinculoOut(
                id=v.id,
                empresa=EmpresaRef.model_validate(v.empresa),
                matricula=v.matricula,
                cargo=v.cargo,
                data_admissao=v.data_admissao,
                salario_bruto=float(v.salario_bruto),
                margem_disponivel=float(v.margem_disponivel),
                importacao_id=v.ultima_importacao_id,
            )
            for v in c.vinculos
        ],
        criado_em=c.criado_em,
        atualizado_em=c.atualizado_em,
        ultima_importacao_id=c.ultima_importacao_id,
    )


@router.get("/{cliente_id}", response_model=ClienteOut)
def obter(db: Db, cliente_id: int) -> ClienteOut:
    return cliente_out(_carregar(db, cliente_id))


@router.put("/{cliente_id}", response_model=ClienteOut)
def atualizar(db: Db, cliente_id: int, dados: ClienteIn) -> ClienteOut:
    cliente = _carregar(db, cliente_id)
    antes = {k: getattr(cliente, k) for k in historico.CAMPOS_CADASTRO}
    e = dados.endereco
    cliente.nome = dados.nome
    cliente.nome_busca = chave_busca(dados.nome)
    cliente.data_nascimento = dados.data_nascimento
    cliente.sexo = dados.sexo
    cliente.estado_civil = dados.estado_civil
    cliente.email = dados.email
    cliente.telefone = dados.telefone
    cliente.cep, cliente.logradouro, cliente.numero = e.cep, e.logradouro, e.numero
    cliente.complemento, cliente.bairro, cliente.cidade, cliente.uf = e.complemento, e.bairro, e.cidade, e.uf
    mudancas = historico.comparar(
        historico.CAMPOS_CADASTRO, antes, {k: getattr(cliente, k) for k in historico.CAMPOS_CADASTRO}
    )
    if mudancas:
        historico.registrar(
            db,
            [
                {
                    "cliente_id": cliente.id,
                    "origem": "EDICAO",
                    "acao": "ATUALIZACAO",
                    "descricao": "Edição manual",
                    "mudancas": mudancas,
                }
            ],
        )
    cliente.editado_em = func.now()
    cliente.atualizado_em = func.now()
    db.commit()
    return cliente_out(_carregar(db, cliente_id))


@router.delete("/{cliente_id}", status_code=204)
def excluir(db: Db, cliente_id: int) -> Response:
    cliente = _carregar(db, cliente_id)
    cliente.excluido_em = func.now()
    db.commit()
    return Response(status_code=204)


@router.get("/{cliente_id}/historico", response_model=Paginado[AlteracaoOut])
def historico_do_cliente(
    db: Db, cliente_id: int, pagina: int = Query(1, ge=1), tamanho: int = Query(20, ge=1, le=100)
) -> Paginado[AlteracaoOut]:
    _carregar(db, cliente_id)
    filtro = AlteracaoCliente.cliente_id == cliente_id
    total = db.scalar(select(func.count()).select_from(AlteracaoCliente).where(filtro)) or 0
    itens = db.scalars(
        select(AlteracaoCliente)
        .where(filtro)
        .order_by(AlteracaoCliente.criado_em.desc(), AlteracaoCliente.id.desc())
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    )
    return Paginado(items=[AlteracaoOut.model_validate(a) for a in itens], total=total, pagina=pagina, tamanho=tamanho)
