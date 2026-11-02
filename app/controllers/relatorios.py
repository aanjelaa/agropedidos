import csv
import io
from datetime import date, datetime

from flask import Blueprint, Response, render_template, request
from flask_login import login_required
from sqlalchemy import func

from ..extensions import db
from ..models import Categoria, Cliente, ItemPedido, Pedido, Produto

bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


def _periodo():
    hoje = date.today()
    try:
        inicio = datetime.strptime(request.args.get("inicio", ""), "%Y-%m-%d").date()
    except ValueError:
        inicio = hoje.replace(day=1)
    try:
        fim = datetime.strptime(request.args.get("fim", ""), "%Y-%m-%d").date()
    except ValueError:
        fim = hoje
    return inicio, fim


def _pedidos_faturados(inicio, fim):
    return (Pedido.query.filter(Pedido.status.in_(["FATURADO", "ENTREGUE"]),
                                Pedido.data_faturamento.between(inicio, fim))
            .order_by(Pedido.data_faturamento, Pedido.id).all())


@bp.route("/faturamento")
@login_required
def faturamento():
    inicio, fim = _periodo()
    pedidos = _pedidos_faturados(inicio, fim)
    por_cliente = (db.session.query(Cliente.nome, func.count(Pedido.id), func.sum(Pedido.valor_total))
                   .join(Pedido).filter(Pedido.id.in_([p.id for p in pedidos]))
                   .group_by(Cliente.nome).order_by(func.sum(Pedido.valor_total).desc()).all())
    por_categoria = (db.session.query(Categoria.nome, func.sum(ItemPedido.subtotal))
                     .join(Produto, Produto.categoria_id == Categoria.id)
                     .join(ItemPedido, ItemPedido.produto_id == Produto.id)
                     .filter(ItemPedido.pedido_id.in_([p.id for p in pedidos]))
                     .group_by(Categoria.nome).order_by(func.sum(ItemPedido.subtotal).desc()).all())
    total = sum((p.valor_total for p in pedidos), 0)
    return render_template("relatorios/faturamento.html", pedidos=pedidos, inicio=inicio, fim=fim,
                           por_cliente=por_cliente, por_categoria=por_categoria, total=total)


@bp.route("/faturamento.csv")
@login_required
def faturamento_csv():
    inicio, fim = _periodo()
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["Pedido", "NF", "Data faturamento", "Cliente", "CPF/CNPJ", "Valor total"])
    for p in _pedidos_faturados(inicio, fim):
        escritor.writerow([p.numero, p.numero_nf, p.data_faturamento.strftime("%d/%m/%Y"),
                           p.cliente.nome, p.cliente.cpf_cnpj, str(p.valor_total).replace(".", ",")])
    nome = f"faturamento_{inicio:%Y%m%d}_{fim:%Y%m%d}.csv"
    return Response("﻿" + saida.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={nome}"})
