from ..extensions import db


class Categoria(db.Model):
    __tablename__ = "categoria"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False, unique=True)

    produtos = db.relationship("Produto", back_populates="categoria")

    def __repr__(self):
        return self.nome
