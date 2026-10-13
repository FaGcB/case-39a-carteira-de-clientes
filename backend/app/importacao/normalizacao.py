import re
import unicodedata
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

UFS = frozenset("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())

_EPOCA_EXCEL = date(1899, 12, 30)


class ValorInvalido(ValueError):
    pass


def vazio(valor: object) -> bool:
    return valor is None or (isinstance(valor, str) and valor.strip() == "")


def texto(valor: object) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return re.sub(r"\s+", " ", str(valor)).strip()


def somente_digitos(valor: object) -> str:
    return re.sub(r"\D", "", texto(valor))


def _documento(valor: object, tamanho: int) -> str:
    if isinstance(valor, (int, float)):
        return somente_digitos(valor).zfill(tamanho)
    return somente_digitos(valor)


def cpf_valido(cpf: str) -> bool:
    if not re.fullmatch(r"\d{11}", cpf) or len(set(cpf)) == 1:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10) % 11 % 10 != int(cpf[n]):
            return False
    return True


def cnpj_valido(cnpj: str) -> bool:
    if not re.fullmatch(r"\d{14}", cnpj) or len(set(cnpj)) == 1:
        return False
    pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for n in (12, 13):
        soma = sum(int(cnpj[i]) * pesos[i + 13 - n] for i in range(n))
        resto = 11 - soma % 11
        if (0 if resto >= 10 else resto) != int(cnpj[n]):
            return False
    return True


def normalizar_cpf(valor: object) -> str:
    cpf = _documento(valor, 11)
    if not cpf_valido(cpf):
        raise ValorInvalido(f"CPF com dígito verificador inválido ({texto(valor)})")
    return cpf


def normalizar_cnpj(valor: object) -> str:
    cnpj = _documento(valor, 14)
    if not cnpj_valido(cnpj):
        raise ValorInvalido(f"CNPJ com dígito verificador inválido ({texto(valor)})")
    return cnpj


def normalizar_data(valor: object, rotulo: str) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if 1 <= valor < 2958466:
            return _EPOCA_EXCEL + timedelta(days=int(valor))
        raise ValorInvalido(f"{rotulo} inexistente ({texto(valor)})")
    t = texto(valor)
    t = re.sub(r"[ T]\d{2}:\d{2}(:\d{2})?$", "", t)
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        ano, mes, dia = int(m[1]), int(m[2]), int(m[3])
    else:
        m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
        if not m:
            raise ValorInvalido(f"{rotulo} em formato não reconhecido ({t})")
        dia, mes, ano = int(m[1]), int(m[2]), int(m[3])
    try:
        return date(ano, mes, dia)
    except ValueError:
        raise ValorInvalido(f"{rotulo} inexistente ({t})") from None


def normalizar_valor(valor: object, rotulo: str) -> Decimal:
    if isinstance(valor, bool):
        raise ValorInvalido(f"{rotulo} não numérico ({valor})")
    if isinstance(valor, (int, float, Decimal)):
        numero = Decimal(str(valor))
    else:
        t = texto(valor)
        limpo = re.sub(r"(?i)r\$|\s", "", t)
        if "," in limpo and "." in limpo:
            if limpo.rfind(",") > limpo.rfind("."):
                limpo = limpo.replace(".", "").replace(",", ".")
            else:
                limpo = limpo.replace(",", "")
        elif "," in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        elif limpo.count(".") > 1:
            limpo = limpo.replace(".", "")
        if not re.fullmatch(r"-?\d+(\.\d+)?", limpo):
            raise ValorInvalido(f"{rotulo} não numérico ({t or 'vazio'})")
        try:
            numero = Decimal(limpo)
        except InvalidOperation:
            raise ValorInvalido(f"{rotulo} não numérico ({t})") from None
    return numero.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


_PARTICULAS = {"de", "da", "do", "das", "dos", "e"}


def normalizar_nome(valor: object) -> str:
    palavras = texto(valor).lower().split(" ")
    saida = []
    for i, p in enumerate(palavras):
        if i > 0 and p in _PARTICULAS:
            saida.append(p)
        else:
            saida.append("-".join(parte[:1].upper() + parte[1:] for parte in p.split("-")))
    return " ".join(saida)


def chave_busca(valor: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def nome_abreviado(nome: str) -> bool:
    return any(len(p.rstrip(".")) <= 1 or p.endswith(".") for p in nome.split(" ") if p.lower() not in _PARTICULAS)


def nome_mais_completo(atual: str, novo: str) -> str:
    if nome_abreviado(atual) and not nome_abreviado(novo):
        return novo
    return atual


def normalizar_uf(valor: object, rotulo: str) -> str:
    uf = texto(valor).upper()
    if uf not in UFS:
        raise ValorInvalido(f"{rotulo} inexistente ({texto(valor) or 'vazio'})")
    return uf


def normalizar_email(valor: object) -> str | None:
    if vazio(valor):
        return None
    email = texto(valor).lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s.]+(\.[^@\s.]+)+", email) or ".." in email:
        raise ValorInvalido(f"E-mail em formato inválido ({texto(valor)})")
    return email


def normalizar_telefone(valor: object) -> str | None:
    digitos = somente_digitos(valor)
    if digitos.startswith("55") and len(digitos) in (12, 13):
        digitos = digitos[2:]
    return digitos if len(digitos) in (10, 11) else None


def normalizar_cep(valor: object) -> str | None:
    digitos = _documento(valor, 8) if not vazio(valor) else ""
    return digitos if len(digitos) == 8 else None


def normalizar_sexo(valor: object) -> str | None:
    s = texto(valor).upper()[:1]
    return s if s in ("F", "M") else None


def idade_em(nascimento: date, referencia: date) -> int:
    anos = referencia.year - nascimento.year
    if (referencia.month, referencia.day) < (nascimento.month, nascimento.day):
        anos -= 1
    return anos
