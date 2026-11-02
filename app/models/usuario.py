from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"

    PERFIS = {"ADMIN": "Administrador", "VENDEDOR": "Vendedor", "FATURISTA": "Faturista"}

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.Enum("ADMIN", "VENDEDOR", "FATURISTA", name="perfil_usuario"),
                       nullable=False, default="VENDEDOR")
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def definir_senha(self, senha: str):
        if not senha or len(senha) < 6:
            raise ValueError("A senha deve ter pelo menos 6 caracteres.")
        self.senha_hash = generate_password_hash(senha)

    def conferir_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha or "")

    @property
    def is_active(self):  # usado pelo Flask-Login: usuário inativo não entra
        return self.ativo

    @property
    def perfil_nome(self):
        return self.PERFIS.get(self.perfil, self.perfil)

    def pode(self, acao: str) -> bool:
        """Matriz de permissões do sistema (RN09)."""
        permissoes = {
            "gerir_clientes": {"ADMIN", "VENDEDOR"},
            "gerir_produtos": {"ADMIN"},
            "criar_pedido": {"ADMIN", "VENDEDOR"},
            "cancelar_pedido": {"ADMIN", "VENDEDOR"},
            "faturar_pedido": {"ADMIN", "FATURISTA"},
            "entregar_pedido": {"ADMIN", "FATURISTA"},
            "gerir_usuarios": {"ADMIN"},
        }
        return self.perfil in permissoes.get(acao, set())
