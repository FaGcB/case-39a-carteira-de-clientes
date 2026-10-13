import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.erros import registrar_tratadores, resposta_erro
from app.motor.rotas import router as motor
from app.rotas.clientes import router as clientes
from app.rotas.empresas import router as empresas
from app.rotas.importacoes import router as importacoes
from app.rotas.resumo import router as resumo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("api")

app = FastAPI(title="Carteira de clientes 39A", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origens,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)
registrar_tratadores(app)


@app.exception_handler(Exception)
async def _inesperado(request: Request, e: Exception):
    log.exception("erro inesperado em %s %s", request.method, request.url.path)
    return resposta_erro(500, "O servidor encontrou um erro. Tente de novo em instantes.")


@app.get("/api/saude", tags=["saúde"])
def saude() -> dict[str, str]:
    return {"status": "ok"}


for router in (importacoes, clientes, empresas, resumo, motor):
    app.include_router(router)
