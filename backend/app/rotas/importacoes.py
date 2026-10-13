from fastapi import APIRouter, Query, UploadFile
from sqlalchemy import func, select

from app.db import Db
from app.erros import ErroApi
from app.importacao.exclusao import excluir_importacao
from app.importacao.servico import criar_importacao
from app.models import Cliente, Empresa, Importacao, LinhaImportada, LinhaInvalida, Vinculo
from app.schemas import (
    ClienteDaLinha,
    EmpresaDaLinha,
    ExclusaoImportacaoOut,
    ImportacaoOut,
    LinhaImportadaOut,
    LinhaInvalidaOut,
    LinhasImportadasOut,
    Paginado,
    ResultadoLinha,
)

router = APIRouter(prefix="/api/importacoes", tags=["importações"])


def importacao_out(i: Importacao) -> ImportacaoOut:
    return ImportacaoOut(
        id=i.id,
        arquivo=i.arquivo_nome,
        status=i.status,
        total_linhas=i.total_linhas,
        processadas=i.processadas,
        importadas=i.importadas,
        invalidas=i.invalidas,
        criada_em=i.criada_em,
        finalizada_em=i.finalizada_em,
        erro=i.erro,
    )


@router.post("", status_code=202, response_model=ImportacaoOut)
async def enviar(db: Db, arquivo: UploadFile) -> ImportacaoOut:
    conteudo = await arquivo.read()
    return importacao_out(criar_importacao(db, arquivo.filename or "", conteudo))


@router.get("", response_model=Paginado[ImportacaoOut])
def listar(db: Db, pagina: int = Query(1, ge=1), tamanho: int = Query(10, ge=1, le=100)) -> Paginado[ImportacaoOut]:
    total = db.scalar(select(func.count()).select_from(Importacao)) or 0
    itens = db.scalars(select(Importacao).order_by(Importacao.id.desc()).limit(tamanho).offset((pagina - 1) * tamanho))
    return Paginado(items=[importacao_out(i) for i in itens], total=total, pagina=pagina, tamanho=tamanho)


@router.get("/{importacao_id}", response_model=ImportacaoOut)
def obter(db: Db, importacao_id: int) -> ImportacaoOut:
    imp = db.get(Importacao, importacao_id)
    if imp is None:
        raise ErroApi(404, "Importação não encontrada.")
    return importacao_out(imp)


@router.get("/{importacao_id}/linhas-invalidas", response_model=Paginado[LinhaInvalidaOut])
def linhas_invalidas(
    db: Db, importacao_id: int, pagina: int = Query(1, ge=1), tamanho: int = Query(20, ge=1, le=100)
) -> Paginado[LinhaInvalidaOut]:
    if db.get(Importacao, importacao_id) is None:
        raise ErroApi(404, "Importação não encontrada.")
    filtro = LinhaInvalida.importacao_id == importacao_id
    total = db.scalar(select(func.count()).select_from(LinhaInvalida).where(filtro)) or 0
    linhas = db.scalars(
        select(LinhaInvalida).where(filtro).order_by(LinhaInvalida.linha).limit(tamanho).offset((pagina - 1) * tamanho)
    )
    return Paginado(
        items=[LinhaInvalidaOut.model_validate(item) for item in linhas], total=total, pagina=pagina, tamanho=tamanho
    )


@router.get("/{importacao_id}/linhas-importadas", response_model=LinhasImportadasOut)
def linhas_importadas(
    db: Db,
    importacao_id: int,
    resultado: ResultadoLinha | None = None,
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(20, ge=1, le=100),
) -> LinhasImportadasOut:
    if db.get(Importacao, importacao_id) is None:
        raise ErroApi(404, "Importação não encontrada.")
    da_importacao = LinhaImportada.importacao_id == importacao_id
    por_resultado = {
        r or "SEM_REGISTRO": n
        for r, n in db.execute(
            select(LinhaImportada.resultado, func.count()).where(da_importacao).group_by(LinhaImportada.resultado)
        )
    }
    filtro = [da_importacao] + ([LinhaImportada.resultado == resultado] if resultado else [])
    total = db.scalar(select(func.count()).select_from(LinhaImportada).where(*filtro)) or 0
    linhas = db.execute(
        select(LinhaImportada, Cliente, Empresa, Vinculo.matricula)
        .join(Cliente, Cliente.id == LinhaImportada.cliente_id)
        .join(Vinculo, Vinculo.id == LinhaImportada.vinculo_id)
        .join(Empresa, Empresa.id == Vinculo.empresa_id)
        .where(*filtro)
        .order_by(LinhaImportada.linha.nulls_last(), LinhaImportada.id)
        .limit(tamanho)
        .offset((pagina - 1) * tamanho)
    )
    items = [
        LinhaImportadaOut(
            linha=li.linha,
            resultado=li.resultado,
            cliente=ClienteDaLinha(id=c.id, nome=c.nome, cpf=c.cpf, excluido=c.excluido_em is not None),
            empresa=EmpresaDaLinha(id=e.id, nome_fantasia=e.nome_fantasia, cnpj=e.cnpj),
            matricula=matricula,
        )
        for li, c, e, matricula in linhas
    ]
    return LinhasImportadasOut(items=items, total=total, pagina=pagina, tamanho=tamanho, por_resultado=por_resultado)


@router.get("/{importacao_id}/exclusao", response_model=ExclusaoImportacaoOut)
def previa_exclusao(db: Db, importacao_id: int) -> ExclusaoImportacaoOut:
    try:
        return ExclusaoImportacaoOut(**vars(excluir_importacao(db, importacao_id)))
    finally:
        db.rollback()


@router.delete("/{importacao_id}", response_model=ExclusaoImportacaoOut)
def excluir(db: Db, importacao_id: int) -> ExclusaoImportacaoOut:
    resultado = excluir_importacao(db, importacao_id)
    db.commit()
    return ExclusaoImportacaoOut(**vars(resultado))
