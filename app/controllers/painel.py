from datetime import date

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from ..extensions import db
from ..models import Pedido

bp = Blueprint("painel", __name__)


@bp.route("/")
@login_required
def inicio():
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)

    contagem = dict(db.session.query(Pedido.status, func.count(Pedido.id))
                    .group_by(Pedido.status).all())
    atrasados = (Pedido.query
                 .filter(Pedido.status.in_(["PENDENTE", "FATURADO"]),
                         Pedido.data_prevista_entrega < hoje)
                 .order_by(Pedido.data_prevista_entrega).all())
    faturado_mes = (db.session.query(func.coalesce(func.sum(Pedido.valor_total), 0))
                    .filter(Pedido.status.in_(["FATURADO", "ENTREGUE"]),
                            Pedido.data_faturamento >= inicio_mes).scalar())
    carteira_pendente = (db.session.query(func.coalesce(func.sum(Pedido.valor_total), 0))
                         .filter(Pedido.status == "PENDENTE").scalar())
    vencem_hoje = Pedido.query.filter(Pedido.status.in_(["PENDENTE", "FATURADO"]),
                                      Pedido.data_prevista_entrega == hoje).count()
    return render_template("painel.html", contagem=contagem, atrasados=atrasados,
                           faturado_mes=faturado_mes, carteira_pendente=carteira_pendente,
                           vencem_hoje=vencem_hoje, hoje=hoje)
