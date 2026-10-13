from dataclasses import dataclass

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.orm import Session

from app.erros import ErroApi
from app.models import Cliente, Empresa, Importacao, Vinculo, vinculo_importacoes

vi = vinculo_importacoes


@dataclass(frozen=True)
class ResultadoExclusao:
    importacao_id: int
    arquivo: str
    vinculos_removidos: int
    clientes_removidos: int
    clientes_mantidos: int
    empresas_removidas: int
    linhas_rejeitadas_removidas: int


def excluir_importacao(db: Session, importacao_id: int) -> ResultadoExclusao:
    imp = db.scalar(select(Importacao).where(Importacao.id == importacao_id).with_for_update())
    if imp is None:
        raise ErroApi(404, "Importação não encontrada.")
    if imp.status in ("PENDENTE", "PROCESSANDO"):
        raise ErroApi(409, "Esta importação ainda está em andamento. Espere terminar para apagar.")

    vinculos_ids = list(db.scalars(select(vi.c.vinculo_id).where(vi.c.importacao_id == importacao_id)))
    clientes_ids = list(db.scalars(select(Vinculo.cliente_id).where(Vinculo.id.in_(vinculos_ids)).distinct()))
    empresas_ids = list(db.scalars(select(Vinculo.empresa_id).where(Vinculo.id.in_(vinculos_ids)).distinct()))

    db.execute(delete(vi).where(vi.c.importacao_id == importacao_id))

    sem_outra_importacao = ~exists().where(vi.c.vinculo_id == Vinculo.id)
    vinculos_removidos = db.execute(
        delete(Vinculo).where(Vinculo.id.in_(vinculos_ids), sem_outra_importacao).returning(Vinculo.id)
    ).all()

    sem_vinculo_cliente = ~exists().where(Vinculo.cliente_id == Cliente.id)
    clientes_removidos = db.execute(
        delete(Cliente).where(Cliente.id.in_(clientes_ids), sem_vinculo_cliente).returning(Cliente.id)
    ).all()

    sem_vinculo_empresa = ~exists().where(Vinculo.empresa_id == Empresa.id)
    empresas_removidas = db.execute(
        delete(Empresa).where(Empresa.id.in_(empresas_ids), sem_vinculo_empresa).returning(Empresa.id)
    ).all()

    _recalcular_origem(db, importacao_id)

    linhas_rejeitadas = imp.invalidas
    arquivo = imp.arquivo_nome
    db.delete(imp)
    db.flush()

    return ResultadoExclusao(
        importacao_id=importacao_id,
        arquivo=arquivo,
        vinculos_removidos=len(vinculos_removidos),
        clientes_removidos=len(clientes_removidos),
        clientes_mantidos=len(clientes_ids) - len(clientes_removidos),
        empresas_removidas=len(empresas_removidas),
        linhas_rejeitadas_removidas=linhas_rejeitadas,
    )


def _recalcular_origem(db: Session, importacao_id: int) -> None:

    def primeira_e_ultima(alvo):
        if alvo is Vinculo:
            base = select(vi.c.importacao_id).where(vi.c.vinculo_id == Vinculo.id)
        else:
            coluna = Vinculo.cliente_id if alvo is Cliente else Vinculo.empresa_id
            base = select(vi.c.importacao_id).join(Vinculo, Vinculo.id == vi.c.vinculo_id).where(coluna == alvo.id)
        menor = base.with_only_columns(func.min(vi.c.importacao_id)).scalar_subquery()
        maior = base.with_only_columns(func.max(vi.c.importacao_id)).scalar_subquery()
        return menor, maior

    for modelo in (Vinculo, Cliente, Empresa):
        menor, maior = primeira_e_ultima(modelo)
        afetados = (modelo.importacao_origem_id == importacao_id) | (modelo.ultima_importacao_id == importacao_id)
        valores: dict = {"importacao_origem_id": menor, "ultima_importacao_id": maior}
        if modelo is Cliente:
            valores["ultima_importacao_em"] = (
                select(Importacao.criada_em).where(Importacao.id == maior).scalar_subquery()
            )
        db.execute(update(modelo).where(afetados).values(**valores).execution_options(synchronize_session=False))
