from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..models import Usuario

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("painel.inicio"))
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario or not usuario.conferir_senha(request.form.get("senha")):
            flash("E-mail ou senha incorretos.", "erro")
        elif not usuario.ativo:
            flash("Usuário inativo. Procure o administrador.", "erro")
        else:
            login_user(usuario)
            flash(f"Bem-vindo(a), {usuario.nome}!", "sucesso")
            destino = request.args.get("next")
            if not destino or not destino.startswith("/"):
                destino = url_for("painel.inicio")
            return redirect(destino)
    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("auth.login"))
