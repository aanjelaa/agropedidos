from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db
from ..models import Usuario
from ..utils.seguranca import perfil_requerido
from ..utils.validadores import email_valido

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.route("/")
@perfil_requerido("ADMIN")
def listar():
    return render_template("usuarios/lista.html", usuarios=Usuario.query.order_by(Usuario.nome).all())


@bp.route("/novo", methods=["GET", "POST"])
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@perfil_requerido("ADMIN")
def formulario(id=None):
    usuario = db.session.get(Usuario, id) if id else Usuario(perfil="VENDEDOR")
    if id and not usuario:
        abort(404)
    if request.method == "POST":
        erros = []
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        perfil = request.form.get("perfil")
        senha = request.form.get("senha") or ""
        if len(nome) < 3:
            erros.append("Informe o nome.")
        if not email_valido(email):
            erros.append("E-mail inválido.")
        elif Usuario.query.filter(Usuario.email == email, Usuario.id != (id or 0)).first():
            erros.append("Este e-mail já está em uso.")
        if perfil not in Usuario.PERFIS:
            erros.append("Selecione o perfil.")
        if not id or senha:
            if len(senha) < 6:
                erros.append("A senha deve ter pelo menos 6 caracteres.")
        if id == current_user.id and perfil != "ADMIN":
            erros.append("Você não pode remover seu próprio perfil de administrador.")
        if erros:
            for e in erros:
                flash(e, "erro")
            usuario_tela = Usuario(id=id, nome=nome, email=email, perfil=perfil)
            return render_template("usuarios/form.html", usuario=usuario_tela, editando=bool(id))
        usuario.nome, usuario.email, usuario.perfil = nome, email, perfil
        if senha:
            usuario.definir_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        flash("Usuário salvo com sucesso.", "sucesso")
        return redirect(url_for("usuarios.listar"))
    return render_template("usuarios/form.html", usuario=usuario, editando=bool(id))


@bp.route("/<int:id>/alternar", methods=["POST"])
@perfil_requerido("ADMIN")
def alternar(id):
    usuario = db.get_or_404(Usuario, id)
    if usuario.id == current_user.id:
        flash("Você não pode inativar o seu próprio usuário.", "erro")
    else:
        usuario.ativo = not usuario.ativo
        db.session.commit()
        flash(f"Usuário {'reativado' if usuario.ativo else 'inativado'}.", "sucesso")
    return redirect(url_for("usuarios.listar"))
