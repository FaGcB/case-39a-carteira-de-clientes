import hashlib

from sqlalchemy.orm import Session

from app.config import config
from app.erros import ErroApi
from app.models import Importacao

EXTENSOES = (".xlsx", ".csv")


def criar_importacao(sessao: Session, nome_arquivo: str, conteudo: bytes) -> Importacao:
    nome = (nome_arquivo or "").strip()
    if not nome.lower().endswith(EXTENSOES):
        raise ErroApi(422, "Formato não suportado.", {"arquivo": "Envie um arquivo .xlsx ou .csv."})
    if not conteudo:
        raise ErroApi(422, "O arquivo está vazio.", {"arquivo": "O arquivo enviado está vazio."})
    limite = config.tamanho_maximo_arquivo_mb * 1024 * 1024
    if len(conteudo) > limite:
        raise ErroApi(413, "Arquivo grande demais.", {"arquivo": f"O limite é {config.tamanho_maximo_arquivo_mb} MB."})
    if nome.lower().endswith(".xlsx") and not conteudo.startswith(b"PK"):
        raise ErroApi(422, "Arquivo inválido.", {"arquivo": "O arquivo não é um .xlsx válido."})

    importacao = Importacao(
        arquivo_nome=nome[:255],
        arquivo_hash=hashlib.sha256(conteudo).hexdigest(),
        conteudo=conteudo,
        status="PENDENTE",
    )
    sessao.add(importacao)
    sessao.commit()
    return importacao
