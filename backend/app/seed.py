import sys
from pathlib import Path

from app.db import SessionLocal
from app.importacao.processador import identificador_worker, processar, reivindicar
from app.importacao.servico import criar_importacao


def main(caminho: str) -> None:
    arquivo = Path(caminho)
    with SessionLocal() as sessao:
        imp = criar_importacao(sessao, arquivo.name, arquivo.read_bytes())
        worker_id = f"seed-{identificador_worker()}"
        if reivindicar(sessao, worker_id, importacao_id=imp.id) is None:
            sys.exit(f"Não foi possível processar a importação {imp.id}.")
        processar(sessao, imp.id, worker_id)
        sessao.refresh(imp)
        print(
            f"Importação #{imp.id} ({imp.arquivo_nome}): {imp.status.lower()} — "
            f"{imp.total_linhas} linhas, {imp.importadas} importadas, {imp.invalidas} rejeitadas."
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("uso: python -m app.seed <arquivo .xlsx ou .csv>")
    main(sys.argv[1])
