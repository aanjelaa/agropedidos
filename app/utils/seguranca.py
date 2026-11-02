"""Controle de acesso por perfil e proteção CSRF simples."""
import secrets
from functools import wraps

from flask import abort, request, session
from flask_login import current_user


def perfil_requerido(*perfis):
    """Decorator: só permite o acesso se o usuário tiver um dos perfis."""
    def decorador(func):
        @wraps(func)
        def envolvido(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.perfil not in perfis:
                abort(403)
            return func(*args, **kwargs)
        return envolvido
    return decorador


def gerar_csrf_token() -> str:
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def verificar_csrf():
    if request.method == "POST":
        enviado = request.form.get("_csrf")
        if not enviado or enviado != session.get("_csrf"):
            abort(400, description="Token de segurança inválido. Recarregue a página.")
