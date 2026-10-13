from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import Db
from app.erros import ErroApi
from app.importacao.normalizacao import chave_busca, somente_digitos
from app.models import Cliente, Empresa, Vinculo
from app.schemas import ClienteRef, EmpresaIn, EmpresaOut, Paginado, VinculoDaEmpresaOut

router = APIRouter(prefix="/api/empresas", tags=["empresas"])


def _vinculos_ativos():
    return (
        select(
            Vinculo.empresa_id,
            func.count().label("total"),
            func.sum(Vinculo.margem_disponivel).label("margem"),
        )
        .join(Cliente, Cliente.id == Vinculo.cliente_id)
        .where(Cliente.excluido_em.is_(None))
        .group_by(Vinculo.empresa_id)
        .subquery()
    )


def _out(e: Empresa, total: int | None, margem=None) -> EmpresaOut:
    return EmpresaOut(
        id=e.id,
        cnpj=e.cnpj,
        razao_social=e.razao_social,
        nome_fantasia=e.nome_fantasia,
        setor=e.setor,
        cidade=e.cidade,
        uf=e.uf,
        total_vinculos=total or 0,
        margem_total=float(margem or 0),
    )


@router.get("", response_model=Paginado[EmpresaOut])
def listar(
    db: Db,
    busca: str | None = Query(None, max_length=150),
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
) -> Paginado[EmpresaOut]:
    filtros = []
    if busca and busca.strip():
        termo = f"%{busca.strip()}%"
        condicoes = [Empresa.razao_social.ilike(termo), Empresa.nome_fantasia.ilike(termo)]
        if digitos := somente_digitos(busca):
            condicoes.append(Empresa.cnpj.like(f"{digitos}%"))
        filtros.append(or_(*condicoes))
    total = db.scalar(select(func.count(Empresa.id)).where(*filtros)) or 0
    vinculos = _vinculos_ativos()
    linhas = db.execute(
        select(Empresa, vinculos.c.total, vinculos.c.margem)
        .outerjoin(vinculos, vinculos.c.empresa_id == Empresa.id)
        .where(*filtros)
        .order_by(Empresa.razao_social, Empresa.id)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    ).all()
    return Paginado(items=[_out(*linha) for linha in linhas], total=total, pagina=pagina, tamanho=tamanho)


def _obter(db: Session, empresa_id: int) -> EmpresaOut:
    vinculos = _vinculos_ativos()
    linha = db.execute(
        select(Empresa, vinculos.c.total, vinculos.c.margem)
        .outerjoin(vinculos, vinculos.c.empresa_id == Empresa.id)
        .where(Empresa.id == empresa_id)
        .execution_options(populate_existing=True)
    ).first()
    if linha is None:
        raise ErroApi(404, "Empresa não encontrada.")
    return _out(*linha)


@router.get("/{empresa_id}", response_model=EmpresaOut)
def obter(db: Db, empresa_id: int) -> EmpresaOut:
    return _obter(db, empresa_id)


@router.get("/{empresa_id}/vinculos", response_model=Paginado[VinculoDaEmpresaOut])
def vinculos(
    db: Db,
    empresa_id: int,
    nome: str | None = Query(None, max_length=150),
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
) -> Paginado[VinculoDaEmpresaOut]:
    if db.get(Empresa, empresa_id) is None:
        raise ErroApi(404, "Empresa não encontrada.")
    filtros = [Vinculo.empresa_id == empresa_id, Cliente.excluido_em.is_(None)]
    for termo in chave_busca(nome or "").split():
        filtros.append(Cliente.nome_busca.like(f"%{termo}%"))
    base = select(Vinculo, Cliente).join(Cliente, Cliente.id == Vinculo.cliente_id).where(*filtros)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    linhas = db.execute(
        base.order_by(Cliente.nome_busca, Vinculo.id).limit(tamanho).offset((pagina - 1) * tamanho)
    ).all()
    return Paginado(
        items=[
            VinculoDaEmpresaOut(
                id=v.id,
                cliente=ClienteRef(id=c.id, nome=c.nome, cpf=c.cpf),
                matricula=v.matricula,
                cargo=v.cargo,
                data_admissao=v.data_admissao,
                salario_bruto=float(v.salario_bruto),
                margem_disponivel=float(v.margem_disponivel),
            )
            for v, c in linhas
        ],
        total=total,
        pagina=pagina,
        tamanho=tamanho,
    )


@router.put("/{empresa_id}", response_model=EmpresaOut)
def atualizar(db: Db, empresa_id: int, dados: EmpresaIn) -> EmpresaOut:
    empresa = db.get(Empresa, empresa_id)
    if empresa is None:
        raise ErroApi(404, "Empresa não encontrada.")
    empresa.razao_social = dados.razao_social
    empresa.nome_fantasia = dados.nome_fantasia
    empresa.setor = dados.setor
    empresa.editado_em = func.now()
    empresa.atualizado_em = func.now()
    db.commit()
    return _obter(db, empresa_id)
