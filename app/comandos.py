"""Comandos de linha: flask --app run init-db | seed"""
import random
from decimal import Decimal
from datetime import date, datetime, time, timedelta

import click

from .extensions import db


def _gerar_cpf(semente):
    rnd = random.Random(semente)
    base = [rnd.randint(0, 9) for _ in range(9)]
    for tamanho in (9, 10):
        soma = sum(base[i] * (tamanho + 1 - i) for i in range(tamanho))
        base.append((soma * 10) % 11 % 10)
    return "".join(map(str, base))


def _gerar_cnpj(semente):
    rnd = random.Random(semente)
    base = [rnd.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for pesos in (pesos1, [6] + pesos1):
        resto = sum(base[i] * pesos[i] for i in range(len(pesos))) % 11
        base.append(0 if resto < 2 else 11 - resto)
    return "".join(map(str, base))


def criar_banco():
    from .models import Categoria
    db.create_all()
    for nome in ("Sementes", "Defensivos", "Fertilizantes"):
        if not Categoria.query.filter_by(nome=nome).first():
            db.session.add(Categoria(nome=nome))
    db.session.commit()


def popular_exemplo():
    from .models import Categoria, Cliente, Pedido, Produto, Usuario

    criar_banco()
    if Usuario.query.first():
        return False

    usuarios = {}
    for nome, email, perfil, senha in [
        ("Administrador", "admin@agropedidos.com", "ADMIN", "admin123"),
        ("Carlos Vendedor", "vendedor@agropedidos.com", "VENDEDOR", "vendedor123"),
        ("Fernanda Faturista", "faturista@agropedidos.com", "FATURISTA", "faturista123"),
    ]:
        u = Usuario(nome=nome, email=email, perfil=perfil)
        u.definir_senha(senha)
        db.session.add(u)
        usuarios[perfil] = u

    clientes = []
    dados_clientes = [
        ("João Batista Ferreira", "F", "Fazenda Santa Luzia", "Rio Verde", "GO"),
        ("Maria Aparecida Rocha", "F", "Sítio Boa Esperança", "Jataí", "GO"),
        ("Agropecuária Vale do Araguaia Ltda", "J", "Fazenda Araguaia", "Barra do Garças", "MT"),
        ("Antônio Carlos Mendes", "F", "Fazenda Três Irmãos", "Uberlândia", "MG"),
        ("Grãos do Cerrado S/A", "J", "Fazenda Cerrado Vivo", "Sorriso", "MT"),
        ("Luiz Fernando Prado", "F", "Fazenda Primavera", "Dourados", "MS"),
    ]
    for i, (nome, tipo, prop, cidade, uf) in enumerate(dados_clientes):
        doc = _gerar_cpf(i + 10) if tipo == "F" else _gerar_cnpj(i + 10)
        c = Cliente(nome=nome, tipo_pessoa=tipo, cpf_cnpj=doc, propriedade=prop, cidade=cidade,
                    uf=uf, telefone=f"(64) 9{9800 + i}-12{30 + i}",
                    email=f"contato{i + 1}@exemplo.com.br")
        db.session.add(c)
        clientes.append(c)

    cat = {c.nome: c for c in Categoria.query.all()}
    produtos = []
    for codigo, desc, categoria, un, preco in [
        ("SEM-001", "Semente de Soja RR 60 kg", "Sementes", "SC", "385.00"),
        ("SEM-002", "Semente de Milho Híbrido 20 kg", "Sementes", "SC", "920.00"),
        ("SEM-003", "Semente de Sorgo Granífero 20 kg", "Sementes", "SC", "310.00"),
        ("DEF-001", "Herbicida Glifosato 480 SL", "Defensivos", "L", "32.50"),
        ("DEF-002", "Fungicida Azoxistrobina + Ciproconazol", "Defensivos", "L", "148.90"),
        ("DEF-003", "Inseticida Clorantraniliprole", "Defensivos", "L", "412.00"),
        ("FER-001", "Fertilizante NPK 04-14-08", "Fertilizantes", "TON", "3150.00"),
        ("FER-002", "Cloreto de Potássio (KCl)", "Fertilizantes", "TON", "2890.00"),
        ("FER-003", "Ureia Agrícola 45%", "Fertilizantes", "TON", "2640.00"),
    ]:
        p = Produto(codigo=codigo, descricao=desc, categoria=cat[categoria], unidade=un,
                    preco_unitario=Decimal(preco))
        db.session.add(p)
        produtos.append(p)
    db.session.flush()

    hoje = date.today()
    rnd = random.Random(42)
    # (dias atrás do pedido, prazo em dias, status final)
    roteiro = [(40, 10, "ENTREGUE"), (35, 15, "ENTREGUE"), (30, 10, "FATURADO"),
               (25, 7, "PENDENTE"), (20, 5, "PENDENTE"), (18, 30, "FATURADO"),
               (12, 20, "PENDENTE"), (10, 3, "FATURADO"), (8, 15, "CANCELADO"),
               (5, 10, "PENDENTE"), (3, 12, "PENDENTE"), (1, 20, "PENDENTE")]
    nf = 1500
    for n, (atras, prazo, status) in enumerate(roteiro):
        data_ped = hoje - timedelta(days=atras)
        pedido = Pedido(vendedor=usuarios["VENDEDOR"], status="PENDENTE")
        itens = [(p.id, rnd.choice([2, 5, 10, 20, 40])) for p in rnd.sample(produtos, rnd.randint(1, 3))]
        pedido.preencher({"cliente_id": clientes[n % len(clientes)].id,
                          "data_pedido": data_ped.isoformat(),
                          "data_prevista_entrega": (data_ped + timedelta(days=prazo)).isoformat()},
                         itens)
        db.session.add(pedido)
        db.session.flush()
        # As datas de faturamento/entrega acompanham a data do pedido, para o
        # histórico de demonstração ficar coerente (correção do defeito D02).
        data_fat = min(data_ped + timedelta(days=2), hoje)
        if status in ("FATURADO", "ENTREGUE"):
            nf += 1
            pedido.alterar_status("FATURADO", usuarios["FATURISTA"], numero_nf=str(nf))
            pedido.data_faturamento = data_fat
            pedido.historico[-1].data_hora = datetime.combine(data_fat, time(10, 30))
        if status == "ENTREGUE":
            pedido.alterar_status("ENTREGUE", usuarios["FATURISTA"])
            pedido.data_entrega = min(data_ped + timedelta(days=prazo - 1), hoje)
            pedido.historico[-1].data_hora = datetime.combine(pedido.data_entrega, time(15, 0))
        if status == "CANCELADO":
            pedido.alterar_status("CANCELADO", usuarios["ADMIN"], observacao="Cliente desistiu da compra.")
            pedido.historico[-1].data_hora = datetime.combine(data_ped + timedelta(days=1), time(9, 0))
    db.session.commit()
    return True


def registrar_comandos(app):
    @app.cli.command("init-db")
    def init_db():
        """Cria as tabelas e as categorias padrão."""
        criar_banco()
        click.echo("Banco de dados criado.")

    @app.cli.command("seed")
    def seed():
        """Cria usuários, clientes, produtos e pedidos de exemplo."""
        if popular_exemplo():
            click.echo("Dados de exemplo inseridos. Login: admin@agropedidos.com / admin123")
        else:
            click.echo("O banco já possui dados; nada foi alterado.")
