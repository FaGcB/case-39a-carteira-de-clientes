import logging
import os
import socket
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, undefer

from app import historico
from app.config import config
from app.importacao.leitura import ArquivoInvalido, ler_planilha
from app.importacao.normalizacao import chave_busca, nome_mais_completo
from app.importacao.validacao import LinhaRejeitada, LinhaValida, validar_linha
from app.models import Cliente, Empresa, Importacao, LinhaImportada, LinhaInvalida, Vinculo, vinculo_importacoes

log = logging.getLogger("importacao")
FUSO = ZoneInfo("America/Sao_Paulo")


def identificador_worker() -> str:
    return f"{socket.gethostname()}-{os.getpid()}"


class ImportacaoPerdida(Exception):
    pass


def reivindicar(sessao: Session, worker_id: str, importacao_id: int | None = None) -> int | None:
    filtro_id = "AND id = :id" if importacao_id is not None else ""
    linha = sessao.execute(
        text(
            f"""
            UPDATE importacoes
               SET status = 'PROCESSANDO', worker_id = :worker, heartbeat_em = now(),
                   iniciada_em = coalesce(iniciada_em, now()), tentativas = tentativas + 1
             WHERE id = (
                   SELECT id FROM importacoes
                    WHERE (status = 'PENDENTE'
                           OR (status = 'PROCESSANDO'
                               AND heartbeat_em < now() - make_interval(secs => :lease)))
                          {filtro_id}
                    ORDER BY id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED)
            RETURNING id, tentativas
            """
        ),
        {"worker": worker_id, "lease": config.lease_segundos, "id": importacao_id},
    ).first()
    sessao.commit()
    if linha is None:
        return None
    if linha.tentativas > config.max_tentativas:
        _falhar(sessao, linha.id, f"O processamento falhou {config.max_tentativas} vezes seguidas e foi interrompido.")
        return None
    return linha.id


def _falhar(sessao: Session, importacao_id: int, mensagem: str) -> None:
    sessao.execute(
        update(Importacao)
        .where(Importacao.id == importacao_id)
        .values(status="FALHOU", erro=mensagem, finalizada_em=func.now(), worker_id=None)
    )
    sessao.commit()


def _garantir_posse(sessao: Session, importacao_id: int, worker_id: str) -> Importacao:
    imp = sessao.execute(
        select(Importacao)
        .where(Importacao.id == importacao_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one()
    if imp.worker_id != worker_id or imp.status != "PROCESSANDO":
        raise ImportacaoPerdida(f"importação {importacao_id} foi assumida por {imp.worker_id}")
    return imp


def processar(
    sessao: Session,
    importacao_id: int,
    worker_id: str,
    tamanho_lote: int | None = None,
    apos_lote: Callable[[int], None] | None = None,
) -> None:
    tamanho_lote = tamanho_lote or config.tamanho_lote
    imp = sessao.execute(
        select(Importacao).options(undefer(Importacao.conteudo)).where(Importacao.id == importacao_id)
    ).scalar_one()
    nome_arquivo, conteudo = imp.arquivo_nome, imp.conteudo
    descricao = f"Importação #{importacao_id} ({nome_arquivo})"
    data_referencia: date = imp.criada_em.astimezone(FUSO).date()
    sessao.commit()

    try:
        linhas = ler_planilha(nome_arquivo, conteudo)
    except ArquivoInvalido as e:
        _falhar(sessao, importacao_id, str(e))
        return

    imp = _garantir_posse(sessao, importacao_id, worker_id)
    if imp.total_linhas is None:
        imp.total_linhas = len(linhas)
    inicio = imp.proxima_linha
    sessao.commit()
    if inicio > 0:
        log.info("importação %s retomada a partir da linha %s de %s", importacao_id, inicio, len(linhas))

    while inicio < len(linhas):
        lote = linhas[inicio : inicio + tamanho_lote]
        imp = _garantir_posse(sessao, importacao_id, worker_id)
        resultados = [validar_linha(bruta, data_referencia) for bruta in lote]
        validas = [r for r in resultados if isinstance(r, LinhaValida)]
        conflitos = _aplicar_lote(sessao, validas, importacao_id, descricao)
        rejeitadas = [r for r in resultados if isinstance(r, LinhaRejeitada)] + [
            LinhaRejeitada(r.numero, [conflitos[r.numero]], r.cliente.cpf, r.cliente.nome)
            for r in validas
            if r.numero in conflitos
        ]
        if rejeitadas:
            sessao.execute(
                insert(LinhaInvalida).on_conflict_do_nothing(constraint="uq_linha_invalida"),
                [
                    {
                        "importacao_id": importacao_id,
                        "linha": r.numero,
                        "motivos": r.motivos,
                        "cpf": (r.cpf or "")[:32] or None,
                        "nome": (r.nome or "")[:255] or None,
                    }
                    for r in rejeitadas
                ],
            )
        invalidas = len(rejeitadas)
        importadas = len(lote) - invalidas
        inicio += len(lote)
        imp.importadas += importadas
        imp.invalidas += invalidas
        imp.processadas += len(lote)
        imp.proxima_linha = inicio
        imp.heartbeat_em = func.now()
        sessao.commit()
        if apos_lote:
            apos_lote(inicio)

    imp = _garantir_posse(sessao, importacao_id, worker_id)
    imp.status = "CONCLUIDA"
    imp.finalizada_em = func.now()
    imp.worker_id = None
    imp.erro = None
    sessao.commit()
    log.info("importação %s concluída: %s importadas, %s rejeitadas", importacao_id, imp.importadas, imp.invalidas)


CAMPOS_CADASTRO = (
    "sexo",
    "estado_civil",
    "email",
    "telefone",
    "cep",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cidade",
    "uf",
)


def _aplicar_lote(
    sessao: Session, linhas: list[LinhaValida], importacao_id: int, descricao: str = ""
) -> dict[int, str]:
    if not linhas:
        return {}
    agora = datetime.now(UTC)
    cpfs = {item.cliente.cpf for item in linhas}
    existentes = {
        c.cpf: c
        for c in sessao.scalars(
            select(Cliente).where(Cliente.cpf.in_(cpfs)).with_for_update().execution_options(populate_existing=True)
        )
    }

    estado: dict[str, dict] = {}
    aceitas: list[LinhaValida] = []
    conflitos: dict[int, str] = {}
    for linha in linhas:
        c = linha.cliente
        atual = estado.get(c.cpf)
        if atual is None and (banco := existentes.get(c.cpf)) is not None:
            atual = {
                "id": banco.id,
                "novo": False,
                "excluido_em": banco.excluido_em,
                "editado": banco.editado_em is not None,
                "data_nascimento": banco.data_nascimento,
                "nome": banco.nome,
                "alterado": {},
            }
        if atual is not None:
            if atual["excluido_em"] is not None:
                conflitos[linha.numero] = (
                    f"Cliente excluído da carteira em {atual['excluido_em'].astimezone(FUSO):%d/%m/%Y}; "
                    "a linha não foi reaplicada"
                )
                continue
            if atual["data_nascimento"] != c.data_nascimento:
                conflitos[linha.numero] = (
                    "CPF já cadastrado para outra pessoa: data de nascimento "
                    f"{c.data_nascimento:%d/%m/%Y} diferente de {atual['data_nascimento']:%d/%m/%Y}. "
                    "Revise o CPF com o parceiro"
                )
                continue
            if not atual["editado"]:
                atual["nome"] = nome_mais_completo(atual["nome"], c.nome)
                atual["alterado"] |= {k: getattr(c, k) for k in CAMPOS_CADASTRO if getattr(c, k) is not None}
        else:
            atual = {
                "id": None,
                "novo": True,
                "excluido_em": None,
                "editado": False,
                "data_nascimento": c.data_nascimento,
                "nome": c.nome,
                "alterado": {k: getattr(c, k) for k in CAMPOS_CADASTRO},
            }
        estado[c.cpf] = atual
        aceitas.append(linha)

    if not aceitas:
        return conflitos

    mudancas: dict[str, list[dict]] = defaultdict(list)
    cadastro_mudou: set[str] = set()
    for cpf, st in estado.items():
        if not st["novo"] and not st["editado"]:
            banco = existentes[cpf]
            antes = {k: getattr(banco, k) for k in historico.CAMPOS_CADASTRO}
            mudancas[cpf] += historico.comparar(
                historico.CAMPOS_CADASTRO, antes, {"nome": st["nome"], **st["alterado"]}
            )
            if mudancas[cpf]:
                cadastro_mudou.add(cpf)

    empresas: dict[str, dict] = {}
    for item in aceitas:
        e = item.empresa
        empresas.setdefault(
            e.cnpj,
            {
                "cnpj": e.cnpj,
                "razao_social": e.razao_social,
                "nome_fantasia": e.nome_fantasia,
                "setor": e.setor,
                "cidade": e.cidade,
                "uf": e.uf,
                "importacao_origem_id": importacao_id,
                "ultima_importacao_id": importacao_id,
            },
        )
    ins_emp = insert(Empresa)
    id_empresa = dict(
        sessao.execute(
            ins_emp.on_conflict_do_update(
                index_elements=[Empresa.cnpj],
                set_={"ultima_importacao_id": ins_emp.excluded.ultima_importacao_id, "atualizado_em": func.now()},
            ).returning(Empresa.cnpj, Empresa.id),
            list(empresas.values()),
        ).all()
    )

    novos = [
        {
            "cpf": cpf,
            "nome": st["nome"],
            "nome_busca": chave_busca(st["nome"]),
            "data_nascimento": st["data_nascimento"],
            "importacao_origem_id": importacao_id,
            "ultima_importacao_id": importacao_id,
            "ultima_importacao_em": agora,
            **st["alterado"],
        }
        for cpf, st in estado.items()
        if st["novo"]
    ]
    if novos:
        for cpf, id_ in sessao.execute(insert(Cliente).returning(Cliente.cpf, Cliente.id), novos):
            estado[cpf]["id"] = id_
    atualizacoes = [
        {
            "id": st["id"],
            "ultima_importacao_id": importacao_id,
            "ultima_importacao_em": agora,
            "atualizado_em": agora,
            **({} if st["editado"] else {"nome": st["nome"], "nome_busca": chave_busca(st["nome"]), **st["alterado"]}),
        }
        for st in estado.values()
        if not st["novo"]
    ]
    for chaves in {tuple(sorted(a)) for a in atualizacoes}:
        grupo = [a for a in atualizacoes if tuple(sorted(a)) == chaves]
        sessao.execute(update(Cliente), grupo)

    vinculos: dict[tuple, dict] = {}
    for item in aceitas:
        v = item.vinculo
        chave = (estado[item.cliente.cpf]["id"], id_empresa[item.empresa.cnpj], v.matricula)
        vinculos[chave] = {
            "cliente_id": chave[0],
            "empresa_id": chave[1],
            "matricula": v.matricula,
            "cargo": v.cargo,
            "data_admissao": v.data_admissao,
            "salario_bruto": v.salario_bruto,
            "margem_disponivel": v.margem_disponivel,
            "importacao_origem_id": importacao_id,
            "ultima_importacao_id": importacao_id,
        }
    cpf_por_id = {st["id"]: cpf for cpf, st in estado.items()}
    nome_empresa = {id_empresa[item.empresa.cnpj]: item.empresa.nome_fantasia for item in aceitas}
    chaves_antigas = [k for k in vinculos if not estado[cpf_por_id[k[0]]]["novo"]]
    antigos: dict[tuple, dict] = {}
    vinculo_mudou: set[tuple] = set()
    if chaves_antigas:
        for v in sessao.execute(
            select(
                Vinculo.cliente_id,
                Vinculo.empresa_id,
                Vinculo.matricula,
                *(getattr(Vinculo, c) for c in historico.CAMPOS_VINCULO),
            ).where(tuple_(Vinculo.cliente_id, Vinculo.empresa_id, Vinculo.matricula).in_(chaves_antigas))
        ):
            antigos[(v.cliente_id, v.empresa_id, v.matricula)] = v._asdict()
    for chave in chaves_antigas:
        contexto = f"{nome_empresa[chave[1]]} · matrícula {chave[2]}"
        cpf = cpf_por_id[chave[0]]
        if chave not in antigos:
            mudancas[cpf].append(historico.mudanca("vinculo", None, contexto))
        elif diff := historico.comparar(historico.CAMPOS_VINCULO, antigos[chave], vinculos[chave], contexto):
            mudancas[cpf] += diff
            vinculo_mudou.add(chave)

    ins_vinc = insert(Vinculo)
    gravados = sessao.execute(
        ins_vinc.on_conflict_do_update(
            constraint="uq_vinculos_cliente_empresa_matricula",
            set_={
                "cargo": ins_vinc.excluded.cargo,
                "data_admissao": ins_vinc.excluded.data_admissao,
                "salario_bruto": ins_vinc.excluded.salario_bruto,
                "margem_disponivel": ins_vinc.excluded.margem_disponivel,
                "ultima_importacao_id": ins_vinc.excluded.ultima_importacao_id,
                "atualizado_em": func.now(),
            },
        ).returning(Vinculo.cliente_id, Vinculo.empresa_id, Vinculo.matricula, Vinculo.id),
        list(vinculos.values()),
    ).all()
    id_vinculo = {(c, e, m): id_ for c, e, m, id_ in gravados}
    sessao.execute(
        insert(vinculo_importacoes).on_conflict_do_nothing(),
        [{"importacao_id": importacao_id, "vinculo_id": id_} for id_ in id_vinculo.values()],
    )

    vistos_cpf: set[str] = set()
    vistas_chave: set[tuple] = set()
    linhas_aceitas = []
    for item in aceitas:
        cpf = item.cliente.cpf
        chave = (estado[cpf]["id"], id_empresa[item.empresa.cnpj], item.vinculo.matricula)
        if chave in vistas_chave:
            resultado = "REPETIDA"
        elif estado[cpf]["novo"] and cpf not in vistos_cpf:
            resultado = "NOVO_CLIENTE"
        elif estado[cpf]["novo"] or chave not in antigos:
            resultado = "NOVO_VINCULO"
        elif cpf in cadastro_mudou or chave in vinculo_mudou:
            resultado = "ATUALIZADA"
        else:
            resultado = "SEM_MUDANCA"
        vistos_cpf.add(cpf)
        vistas_chave.add(chave)
        linhas_aceitas.append(
            {
                "importacao_id": importacao_id,
                "linha": item.numero,
                "cliente_id": chave[0],
                "vinculo_id": id_vinculo[chave],
                "resultado": resultado,
            }
        )
    sessao.execute(insert(LinhaImportada).on_conflict_do_nothing(constraint="uq_linha_importada"), linhas_aceitas)

    base = {"origem": "IMPORTACAO", "importacao_id": importacao_id, "descricao": descricao, "criado_em": agora}
    historico.registrar(
        sessao,
        [{**base, "cliente_id": st["id"], "acao": "CRIACAO", "mudancas": []} for st in estado.values() if st["novo"]]
        + [
            {**base, "cliente_id": estado[cpf]["id"], "acao": "ATUALIZACAO", "mudancas": lista}
            for cpf, lista in mudancas.items()
            if lista
        ],
    )
    return conflitos


def processar_proxima(sessao: Session, worker_id: str) -> bool:
    importacao_id = reivindicar(sessao, worker_id)
    if importacao_id is None:
        return False
    try:
        processar(sessao, importacao_id, worker_id)
    except ImportacaoPerdida as e:
        sessao.rollback()
        log.warning("%s; abandonando", e)
    except Exception:
        sessao.rollback()
        log.exception("erro inesperado na importação %s; será retomada", importacao_id)
        sessao.execute(
            update(Importacao)
            .where(Importacao.id == importacao_id, Importacao.worker_id == worker_id)
            .values(status="PENDENTE", worker_id=None, erro="Erro inesperado; o processamento será retomado.")
        )
        sessao.commit()
    return True
