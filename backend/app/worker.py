import logging
import signal
import time

from app.config import config
from app.db import SessionLocal
from app.importacao.processador import identificador_worker, processar_proxima

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("worker")

_parar = False


def _sinal(*_: object) -> None:
    global _parar
    _parar = True
    log.info("sinal recebido; encerrando depois da importação atual")


def main() -> None:
    signal.signal(signal.SIGTERM, _sinal)
    signal.signal(signal.SIGINT, _sinal)
    worker_id = identificador_worker()
    log.info("worker %s aguardando importações", worker_id)
    while not _parar:
        try:
            with SessionLocal() as sessao:
                teve_trabalho = processar_proxima(sessao, worker_id)
        except Exception:
            log.exception("falha ao consultar a fila; tentando de novo")
            teve_trabalho = False
        if not teve_trabalho:
            time.sleep(config.intervalo_worker_segundos)


if __name__ == "__main__":
    main()
