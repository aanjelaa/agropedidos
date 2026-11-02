from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Categoria, Cliente, Pedido, Produto, Usuario


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        for nome in ("Sementes", "Defensivos", "Fertilizantes"):
            db.session.add(Categoria(nome=nome))
        for nome, email, perfil in [("Admin", "admin@t.com", "ADMIN"),
                                    ("Vendedor", "vend@t.com", "VENDEDOR"),
                                    ("Faturista", "fat@t.com", "FATURISTA")]:
            u = Usuario(nome=nome, email=email, perfil=perfil)
            u.definir_senha("senha123")
            db.session.add(u)
        db.session.add(Cliente(nome="João da Silva", tipo_pessoa="F", cpf_cnpj="52998224725",
                               cidade="Rio Verde", uf="GO"))
        db.session.add(Produto(codigo="SEM-001", descricao="Semente de Soja", categoria_id=1,
                               unidade="SC", preco_unitario=Decimal("100.00")))
        db.session.add(Produto(codigo="FER-001", descricao="NPK 04-14-08", categoria_id=3,
                               unidade="TON", preco_unitario=Decimal("3000.00")))
        db.session.commit()
        yield app


@pytest.fixture
def cliente_http(app):
    return app.test_client()


def entrar(cliente_http, email):
    return cliente_http.post("/login", data={"email": email, "senha": "senha123"}, follow_redirects=True)


@pytest.fixture
def usuario(app):
    return lambda perfil: Usuario.query.filter_by(perfil=perfil).first()


@pytest.fixture
def novo_pedido(app):
    def criar(prevista=None, itens=((1, 10),)):
        p = Pedido(vendedor_id=2)
        hoje = date.today()
        erros = p.preencher({"cliente_id": 1, "data_pedido": (hoje - timedelta(days=30)).isoformat(),
                             "data_prevista_entrega": (prevista or hoje + timedelta(days=5)).isoformat()},
                            list(itens))
        assert erros == []
        db.session.add(p)
        db.session.commit()
        return p
    return criar
