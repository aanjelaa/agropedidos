from decimal import Decimal, InvalidOperation

from ..extensions import db


class Produto(db.Model):
    __tablename__ = "produto"

    UNIDADES = {"SC": "Saco", "KG": "Quilo", "L": "Litro", "TON": "Tonelada", "UN": "Unidade"}

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    descricao = db.Column(db.String(150), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False)
    unidade = db.Column(db.Enum("SC", "KG", "L", "TON", "UN", name="unidade"), nullable=False)
    preco_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    categoria = db.relationship("Categoria", back_populates="produtos")

    def preencher(self, dados: dict) -> list[str]:
        erros = []
        self.codigo = (dados.get("codigo") or "").strip().upper()
        self.descricao = (dados.get("descricao") or "").strip()
        self.unidade = dados.get("unidade") or ""
        try:
            self.categoria_id = int(dados.get("categoria_id") or 0)
        except ValueError:
            self.categoria_id = 0
        try:
            preco = Decimal(str(dados.get("preco_unitario") or "0").replace(",", "."))
        except InvalidOperation:
            preco = Decimal("0")
        self.preco_unitario = preco

        if not self.codigo:
            erros.append("Informe o código do produto.")
        if len(self.descricao) < 3:
            erros.append("Informe a descrição do produto.")
        if self.unidade not in self.UNIDADES:
            erros.append("Selecione a unidade.")
        if not self.categoria_id:
            erros.append("Selecione a categoria.")
        if preco <= 0:
            erros.append("O preço deve ser maior que zero.")
        with db.session.no_autoflush:
            duplicado = Produto.query.filter(Produto.codigo == self.codigo,
                                             Produto.id != (self.id or 0)).first()
        if self.codigo and duplicado:
            erros.append("Já existe um produto com este código.")
        return erros
