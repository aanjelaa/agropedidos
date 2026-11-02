from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from ..extensions import db
from ..models import Cliente
from ..utils.seguranca import perfil_requerido
from ..utils.validadores import UFS, somente_digitos

bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@bp.route("/")
@login_required
def listar():
    busca = (request.args.get("busca") or "").strip()
    mostrar_inativos = request.args.get("inativos") == "1"
    consulta = Cliente.query
    if busca:
        termo = f"%{busca}%"
        filtros = [Cliente.nome.ilike(termo), Cliente.cidade.ilike(termo),
                   Cliente.propriedade.ilike(termo)]
        if somente_digitos(busca):
            filtros.append(Cliente.cpf_cnpj.like(f"%{somente_digitos(busca)}%"))
        consulta = consulta.filter(or_(*filtros))
    if not mostrar_inativos:
        consulta = consulta.filter_by(ativo=True)
    pagina = consulta.order_by(Cliente.nome).paginate(
        page=request.args.get("pagina", 1, type=int), per_page=15, error_out=False)
    return render_template("clientes/lista.html", pagina=pagina, busca=busca,
                           mostrar_inativos=mostrar_inativos)


@bp.route("/novo", methods=["GET", "POST"])
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@perfil_requerido("ADMIN", "VENDEDOR")
def formulario(id=None):
    cliente = db.session.get(Cliente, id) if id else Cliente(tipo_pessoa="F")
    if id and not cliente:
        abort(404)
    if request.method == "POST":
        erros = cliente.preencher(request.form)
        if erros:
            for e in erros:
                flash(e, "erro")
            # mostra o formulário com o que foi digitado, sem gravar nada
            with db.session.no_autoflush:
                pagina = render_template("clientes/form.html", cliente=cliente, ufs=UFS)
            db.session.rollback()
            return pagina
        else:
            db.session.add(cliente)
            db.session.commit()
            flash("Cliente salvo com sucesso.", "sucesso")
            return redirect(url_for("clientes.listar"))
    return render_template("clientes/form.html", cliente=cliente, ufs=UFS)


@bp.route("/<int:id>/alternar", methods=["POST"])
@perfil_requerido("ADMIN", "VENDEDOR")
def alternar(id):
    """RN10 - cliente não é excluído, apenas inativado (preserva histórico)."""
    cliente = db.get_or_404(Cliente, id)
    cliente.ativo = not cliente.ativo
    db.session.commit()
    flash(f"Cliente {'reativado' if cliente.ativo else 'inativado'}.", "sucesso")
    return redirect(url_for("clientes.listar"))
