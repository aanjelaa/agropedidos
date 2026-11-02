"""Testes de integração das rotas (camada Controller + View)."""
from datetime import date, timedelta

from app.models import Cliente, Pedido
from conftest import entrar


def test_login_invalido(cliente_http):
    r = cliente_http.post("/login", data={"email": "admin@t.com", "senha": "errada"})
    assert "E-mail ou senha incorretos" in r.get_data(as_text=True)


def test_pagina_exige_login(cliente_http):
    r = cliente_http.get("/pedidos/")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_painel_mostra_atrasados(cliente_http, novo_pedido):
    novo_pedido(prevista=date.today() - timedelta(days=2))
    entrar(cliente_http, "admin@t.com")
    html = cliente_http.get("/").get_data(as_text=True)
    assert "Pedidos atrasados" in html and "2 dias" in html


def test_cadastrar_cliente_pela_tela(cliente_http, app):
    entrar(cliente_http, "vend@t.com")
    r = cliente_http.post("/clientes/novo", data={"nome": "Fazenda Nova Ltda", "tipo_pessoa": "J",
                                                  "cpf_cnpj": "11.222.333/0001-81",
                                                  "cidade": "Sorriso", "uf": "MT"}, follow_redirects=True)
    assert "Cliente salvo com sucesso" in r.get_data(as_text=True)
    assert Cliente.query.filter_by(cpf_cnpj="11222333000181").first()


def test_cliente_cpf_invalido_pela_tela(cliente_http):
    entrar(cliente_http, "vend@t.com")
    r = cliente_http.post("/clientes/novo", data={"nome": "Teste", "tipo_pessoa": "F",
                                                  "cpf_cnpj": "123.456.789-00", "cidade": "X", "uf": "GO"})
    assert "CPF inválido" in r.get_data(as_text=True)


def test_lancar_pedido_pela_tela(cliente_http, app):
    entrar(cliente_http, "vend@t.com")
    r = cliente_http.post("/pedidos/novo", data={
        "cliente_id": "1", "data_pedido": date.today().isoformat(),
        "data_prevista_entrega": (date.today() + timedelta(days=7)).isoformat(),
        "produto_id": ["1", "2"], "quantidade": ["10", "1"]}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "criado com sucesso" in html and "R$ 4.000,00" in html


def test_faturista_fatura_pela_tela(cliente_http, novo_pedido):
    p = novo_pedido()
    entrar(cliente_http, "fat@t.com")
    r = cliente_http.post(f"/pedidos/{p.id}/status", data={"novo_status": "FATURADO", "numero_nf": "777"},
                          follow_redirects=True)
    assert "agora está: Faturado" in r.get_data(as_text=True)


def test_faturista_nao_cadastra_produto(cliente_http):
    entrar(cliente_http, "fat@t.com")
    assert cliente_http.get("/produtos/novo").status_code == 403


def test_vendedor_nao_acessa_usuarios(cliente_http):
    entrar(cliente_http, "vend@t.com")
    assert cliente_http.get("/usuarios/").status_code == 403


def test_relatorio_csv(cliente_http, novo_pedido, usuario):
    from app.extensions import db
    p = novo_pedido()
    p.alterar_status("FATURADO", usuario("FATURISTA"), numero_nf="8888")
    db.session.commit()
    entrar(cliente_http, "admin@t.com")
    r = cliente_http.get("/relatorios/faturamento.csv")
    assert r.mimetype == "text/csv" and "8888" in r.get_data(as_text=True)
