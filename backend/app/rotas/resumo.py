from fastapi import APIRouter
from sqlalchemy import func, select

from app.db import Db
from app.models import Cliente, Empresa, Importacao, Vinculo
from app.rotas.importacoes import importacao_out
from app.schemas import EmpresaRef, ResumoOut, VinculosPorEmpresa

router = APIRouter(prefix="/api/resumo", tags=["resumo"])


@router.get("", response_model=ResumoOut)
def resumo(
    db: Db,
) -> ResumoOut:
    ativos = Cliente.excluido_em.is_(None)
    por_empresa = db.execute(
        select(Empresa, func.count(Vinculo.id).label("total"))
        .join(Vinculo, Vinculo.empresa_id == Empresa.id)
        .join(Cliente, Cliente.id == Vinculo.cliente_id)
        .where(ativos)
        .group_by(Empresa.id)
        .order_by(func.count(Vinculo.id).desc(), Empresa.nome_fantasia)
    ).all()
    ultima = db.scalar(select(Importacao).order_by(Importacao.id.desc()).limit(1))
    return ResumoOut(
        clientes=db.scalar(select(func.count(Cliente.id)).where(ativos)) or 0,
        empresas=db.scalar(select(func.count(Empresa.id))) or 0,
        vinculos=sum(total for _, total in por_empresa),
        importacoes=db.scalar(select(func.count(Importacao.id))) or 0,
        linhas_invalidas=db.scalar(select(func.coalesce(func.sum(Importacao.invalidas), 0))) or 0,
        ultima_importacao=importacao_out(ultima) if ultima else None,
        vinculos_por_empresa=[
            VinculosPorEmpresa(empresa=EmpresaRef.model_validate(e), total=total) for e, total in por_empresa
        ],
    )
