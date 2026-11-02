"""Filtros Jinja para exibir valores no padrão brasileiro."""
from decimal import Decimal


def moeda(valor) -> str:
    valor = Decimal(valor or 0)
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def numero(valor, casas=2) -> str:
    valor = Decimal(valor or 0)
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(valor) -> str:
    return valor.strftime("%d/%m/%Y") if valor else "—"


def data_hora_br(valor) -> str:
    return valor.strftime("%d/%m/%Y %H:%M") if valor else "—"


def documento(valor: str) -> str:
    v = valor or ""
    if len(v) == 11:
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
    if len(v) == 14:
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
    return v
