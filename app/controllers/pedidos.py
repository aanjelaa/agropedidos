import json
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Cliente, Pedido, Produto, RegraNegocioErro
from ..utils.seguranca import perfil_requerido

bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


@bp.route("/")
@login_required
def listar():
    status = request.args.get("status") or ""
    busca = (request.args.get("busca") or "").strip()
    so_atrasados = request.args.get("atrasados") == "1"

    consulta = Pedido.query.join(Cliente)
    if status in Pedido.STATUS:
        consulta = consulta.filter(Pedido.status == status)
    if busca:
        if busca.upper().startswith("PV-") and busca[3:].isdigit():
            consulta = consulta.filter(Pedido.id == int(busca[3:]))
        elif busca.isdigit():
            consulta = consulta.filter((Pedido.id == int(busca)) | (Pedido.numero_nf == busca))
        else:
            consulta = consulta.filter(Cliente.nome.ilike(f"%{busca}%"))
    if so_atrasados:
        consulta = consulta.filter(Pedido.status.in_(["PENDENTE", "FATURADO"]),
                                   Pedido.data_prevista_entrega < date.today())
    pagina = consulta.order_by(Pedido.id.desc()).paginate(
        page=request.args.get("pagina", 1, type=int), per_page=15, error_out=False)
    return render_template("pedidos/lista.html", pagina=pagina, status=status, busca=busca,
                           so_atrasados=so_atrasados, status_opcoes=Pedido.STATUS)


@bp.route("/<int:id>")
@login_required
def detalhe(id):
    pedido = db.get_or_404(Pedido, id)
    return render_template("pedidos/detalhe.html", pedido=pedido)


def _render_form(pedido):
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.descricao).all()
    catalogo = {p.id: {"preco": float(p.preco_unitario), "unidade": p.unidade} for p in produtos}
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    return render_template("pedidos/form.html", pedido=pedido, produtos=produtos,
                           clientes=clientes, catalogo_json=json.dumps(catalogo), hoje=date.today())


@bp.route("/novo", methods=["GET", "POST"])
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@perfil_requerido("ADMIN", "VENDEDOR")
def formulario(id=None):
    if id:
        pedido = db.get_or_404(Pedido, id)
        if not pedido.editavel:
            flash("Este pedido não pode mais ser alterado.", "erro")
            return redirect(url_for("pedidos.detalhe", id=id))
    else:
        pedido = Pedido(vendedor_id=current_user.id, data_pedido=date.today())

    if request.method == "POST":
        itens = list(zip(request.form.getlist("produto_id"), request.form.getlist("quantidade")))
        with db.session.no_autoflush:
            erros = pedido.preencher(request.form, itens)
        if erros:
            for e in erros:
                flash(e, "erro")
            with db.session.no_autoflush:
                pagina = _render_form(pedido)
            db.session.rollback()
            return pagina
        novo = pedido.id is None
        db.session.add(pedido)
        db.session.commit()
        flash(f"Pedido {pedido.numero} {'criado' if novo else 'atualizado'} com sucesso.", "sucesso")
        return redirect(url_for("pedidos.detalhe", id=pedido.id))
    return _render_form(pedido)


@bp.route("/<int:id>/status", methods=["POST"])
@login_required
def alterar_status(id):
    pedido = db.get_or_404(Pedido, id)
    novo = request.form.get("novo_status")
    try:
        pedido.alterar_status(novo, current_user, numero_nf=request.form.get("numero_nf", ""),
                              observacao=request.form.get("observacao", ""))
        db.session.commit()
        flash(f"Pedido {pedido.numero} agora está: {pedido.status_nome}.", "sucesso")
    except RegraNegocioErro as erro:
        db.session.rollback()
        flash(str(erro), "erro")
    return redirect(url_for("pedidos.detalhe", id=id))
