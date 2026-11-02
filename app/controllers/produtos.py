from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from ..extensions import db
from ..models import Categoria, Produto
from ..utils.seguranca import perfil_requerido

bp = Blueprint("produtos", __name__, url_prefix="/produtos")


@bp.route("/")
@login_required
def listar():
    busca = (request.args.get("busca") or "").strip()
    categoria_id = request.args.get("categoria", type=int)
    consulta = Produto.query.filter_by(ativo=True) if request.args.get("inativos") != "1" else Produto.query
    if busca:
        consulta = consulta.filter(or_(Produto.descricao.ilike(f"%{busca}%"),
                                       Produto.codigo.ilike(f"%{busca}%")))
    if categoria_id:
        consulta = consulta.filter_by(categoria_id=categoria_id)
    pagina = consulta.order_by(Produto.codigo).paginate(
        page=request.args.get("pagina", 1, type=int), per_page=15, error_out=False)
    return render_template("produtos/lista.html", pagina=pagina, busca=busca,
                           categorias=Categoria.query.order_by(Categoria.nome).all(),
                           categoria_id=categoria_id, mostrar_inativos=request.args.get("inativos") == "1")


@bp.route("/novo", methods=["GET", "POST"])
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@perfil_requerido("ADMIN")
def formulario(id=None):
    produto = db.session.get(Produto, id) if id else Produto()
    if id and not produto:
        abort(404)
    if request.method == "POST":
        erros = produto.preencher(request.form)
        if erros:
            for e in erros:
                flash(e, "erro")
            with db.session.no_autoflush:
                pagina = render_template("produtos/form.html", produto=produto,
                                         categorias=Categoria.query.order_by(Categoria.nome).all(),
                                         unidades=Produto.UNIDADES)
            db.session.rollback()
            return pagina
        else:
            db.session.add(produto)
            db.session.commit()
            flash("Produto salvo com sucesso.", "sucesso")
            return redirect(url_for("produtos.listar"))
    return render_template("produtos/form.html", produto=produto,
                           categorias=Categoria.query.order_by(Categoria.nome).all(),
                           unidades=Produto.UNIDADES)


@bp.route("/<int:id>/alternar", methods=["POST"])
@perfil_requerido("ADMIN")
def alternar(id):
    produto = db.get_or_404(Produto, id)
    produto.ativo = not produto.ativo
    db.session.commit()
    flash(f"Produto {'reativado' if produto.ativo else 'inativado'}.", "sucesso")
    return redirect(url_for("produtos.listar"))
