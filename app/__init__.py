"""AgroPedidos - fábrica da aplicação Flask (padrão MVC).

  Model      -> app/models       (entidades, regras de negócio, persistência)
  View       -> app/templates    (HTML/Jinja) + app/static (CSS/JS)
  Controller -> app/controllers  (rotas: recebem a requisição e decidem a resposta)
"""
from flask import Flask, render_template

from .config import Config
from .extensions import db, login_manager
from .utils import formatadores
from .utils.seguranca import gerar_csrf_token, verificar_csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from .models import Usuario

    @login_manager.user_loader
    def carregar_usuario(user_id):
        return db.session.get(Usuario, int(user_id))

    # Controllers (blueprints)
    from .controllers.auth import bp as auth_bp
    from .controllers.painel import bp as painel_bp
    from .controllers.clientes import bp as clientes_bp
    from .controllers.produtos import bp as produtos_bp
    from .controllers.pedidos import bp as pedidos_bp
    from .controllers.usuarios import bp as usuarios_bp
    from .controllers.relatorios import bp as relatorios_bp
    for bp in (auth_bp, painel_bp, clientes_bp, produtos_bp, pedidos_bp, usuarios_bp, relatorios_bp):
        app.register_blueprint(bp)

    # Filtros de formatação brasileira usados nas views
    app.jinja_env.filters["moeda"] = formatadores.moeda
    app.jinja_env.filters["numero"] = formatadores.numero
    app.jinja_env.filters["data_br"] = formatadores.data_br
    app.jinja_env.filters["data_hora_br"] = formatadores.data_hora_br
    app.jinja_env.filters["documento"] = formatadores.documento
    app.jinja_env.globals["csrf_token"] = gerar_csrf_token

    if not app.config.get("TESTING"):
        app.before_request(verificar_csrf)

    @app.errorhandler(403)
    def proibido(e):
        return render_template("erros/erro.html", codigo=403,
                               mensagem="Seu perfil não tem permissão para acessar esta página."), 403

    @app.errorhandler(404)
    def nao_encontrado(e):
        return render_template("erros/erro.html", codigo=404,
                               mensagem="Página ou registro não encontrado."), 404

    @app.errorhandler(400)
    def requisicao_invalida(e):
        return render_template("erros/erro.html", codigo=400, mensagem=e.description), 400

    from .comandos import registrar_comandos
    registrar_comandos(app)
    return app
