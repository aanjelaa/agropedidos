"""Testes das regras de negócio do pedido (camada Model)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Cliente, Pedido, RegraNegocioErro


def test_total_calculado_pelos_itens(novo_pedido):
    p = novo_pedido(itens=[(1, 10), (2, "2,5")])          # 10 x 100 + 2,5 x 3000
    assert p.valor_total == Decimal("8500.00")


def test_pedido_sem_itens_nao_salva(app):
    p = Pedido(vendedor_id=2)
    erros = p.preencher({"cliente_id": 1, "data_prevista_entrega": date.today().isoformat()}, [])
    assert "Adicione pelo menos um produto ao pedido." in erros


def test_quantidade_zero_rejeitada(app):
    p = Pedido(vendedor_id=2)
    erros = p.preencher({"cliente_id": 1, "data_prevista_entrega": date.today().isoformat()}, [(1, "0")])
    assert any("Quantidade inválida" in e for e in erros)


def test_previsao_anterior_ao_pedido_rejeitada(app):
    p = Pedido(vendedor_id=2)
    ontem = date.today() - timedelta(days=1)
    erros = p.preencher({"cliente_id": 1, "data_pedido": date.today().isoformat(),
                         "data_prevista_entrega": ontem.isoformat()}, [(1, 1)])
    assert any("não pode ser anterior" in e for e in erros)


def test_preco_congelado_no_lancamento(novo_pedido):
    p = novo_pedido()
    p.itens[0].produto.preco_unitario = Decimal("999.00")
    db.session.commit()
    assert p.itens[0].preco_unitario == Decimal("100.00")


def test_fluxo_completo_de_status(novo_pedido, usuario):
    p = novo_pedido()
    p.alterar_status("FATURADO", usuario("FATURISTA"), numero_nf="1001")
    assert p.status == "FATURADO" and p.data_faturamento == date.today()
    p.alterar_status("ENTREGUE", usuario("FATURISTA"))
    assert p.status == "ENTREGUE" and len(p.historico) == 2


def test_faturar_exige_nf(novo_pedido, usuario):
    p = novo_pedido()
    with pytest.raises(RegraNegocioErro, match="nota fiscal"):
        p.alterar_status("FATURADO", usuario("FATURISTA"), numero_nf="")


def test_nf_nao_pode_repetir(novo_pedido, usuario):
    p1, p2 = novo_pedido(), novo_pedido()
    p1.alterar_status("FATURADO", usuario("FATURISTA"), numero_nf="2000")
    db.session.commit()
    with pytest.raises(RegraNegocioErro, match="já foi usada"):
        p2.alterar_status("FATURADO", usuario("FATURISTA"), numero_nf="2000")


def test_nao_pula_etapa(novo_pedido, usuario):
    p = novo_pedido()
    with pytest.raises(RegraNegocioErro):
        p.alterar_status("ENTREGUE", usuario("ADMIN"))


def test_vendedor_nao_fatura(novo_pedido, usuario):
    p = novo_pedido()
    with pytest.raises(RegraNegocioErro, match="permissão"):
        p.alterar_status("FATURADO", usuario("VENDEDOR"), numero_nf="3000")


def test_cancelamento_exige_motivo(novo_pedido, usuario):
    p = novo_pedido()
    with pytest.raises(RegraNegocioErro, match="motivo"):
        p.alterar_status("CANCELADO", usuario("VENDEDOR"))


def test_pedido_faturado_nao_pode_ser_editado(novo_pedido, usuario):
    p = novo_pedido()
    p.alterar_status("FATURADO", usuario("FATURISTA"), numero_nf="4000")
    erros = p.preencher({"cliente_id": 1, "data_prevista_entrega": date.today().isoformat()}, [(1, 1)])
    assert "não pode mais ser alterado" in erros[0]


def test_regra_de_atraso(novo_pedido, usuario):
    atrasado = novo_pedido(prevista=date.today() - timedelta(days=3))
    em_dia = novo_pedido(prevista=date.today())
    assert atrasado.atrasado and atrasado.dias_atraso == 3
    assert not em_dia.atrasado
    atrasado.alterar_status("CANCELADO", usuario("ADMIN"), observacao="teste")
    assert not atrasado.atrasado


def test_cliente_documento_duplicado(app):
    c = Cliente()
    erros = c.preencher({"nome": "Outro", "tipo_pessoa": "F", "cpf_cnpj": "529.982.247-25",
                         "cidade": "Jataí", "uf": "GO"})
    assert any("Já existe um cliente" in e for e in erros)
