from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErroApi(Exception):
    def __init__(
        self,
        status: int,
        mensagem: str,
        erros: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem
        self.erros = erros or {}
        self.headers = headers


def resposta_erro(status: int, mensagem: str, erros: dict[str, str] | None = None, headers=None) -> JSONResponse:
    corpo: dict[str, object] = {"mensagem": mensagem}
    if erros:
        corpo["erros"] = erros
    return JSONResponse(corpo, status_code=status, headers=headers)


_MENSAGENS_PYDANTIC = {
    "missing": "Campo obrigatório.",
    "string_too_short": "Preencha este campo.",
    "string_too_long": "Texto longo demais.",
    "date_from_datetime_parsing": "Informe uma data válida.",
    "date_parsing": "Informe uma data válida.",
    "date_type": "Informe uma data válida.",
    "int_parsing": "Informe um número inteiro.",
    "literal_error": "Valor não permitido.",
    "greater_than_equal": "Valor abaixo do mínimo.",
    "less_than_equal": "Valor acima do máximo.",
}


def _mensagem(erro: dict) -> str:
    if erro.get("type") == "value_error":
        return str(erro.get("msg", "")).removeprefix("Value error, ")
    return _MENSAGENS_PYDANTIC.get(erro.get("type", ""), "Valor inválido.")


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(ErroApi)
    async def _erro_api(_: Request, e: ErroApi) -> JSONResponse:
        return resposta_erro(e.status, e.mensagem, e.erros, e.headers)

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, e: RequestValidationError) -> JSONResponse:
        erros: dict[str, str] = {}
        for item in e.errors():
            caminho = [str(p) for p in item.get("loc", ()) if p not in ("body", "query", "path")]
            erros.setdefault(".".join(caminho) or "geral", _mensagem(item))
        return resposta_erro(422, "Alguns campos precisam de correção.", erros)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException) -> JSONResponse:
        mensagens = {404: "Recurso não encontrado.", 405: "Método não permitido."}
        mensagem = (
            e.detail
            if isinstance(e.detail, str) and e.status_code not in mensagens
            else mensagens.get(e.status_code, str(e.detail))
        )
        return resposta_erro(e.status_code, mensagem)
