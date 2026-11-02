"""Testes unitários das validações de documento (RN01)."""
from app.utils.formatadores import documento, moeda
from app.utils.validadores import cnpj_valido, cpf_valido


def test_cpf_valido():
    assert cpf_valido("529.982.247-25")


def test_cpf_invalido_digito():
    assert not cpf_valido("529.982.247-24")


def test_cpf_repetido_invalido():
    assert not cpf_valido("111.111.111-11")


def test_cnpj_valido():
    assert cnpj_valido("11.222.333/0001-81")


def test_cnpj_invalido():
    assert not cnpj_valido("11.222.333/0001-80")


def test_formatacao_moeda_brasileira():
    assert moeda(1234.5) == "R$ 1.234,50"


def test_formatacao_documento():
    assert documento("52998224725") == "529.982.247-25"
    assert documento("11222333000181") == "11.222.333/0001-81"
