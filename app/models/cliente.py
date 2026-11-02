from datetime import datetime

from ..extensions import db
from ..utils.validadores import UFS, cnpj_valido, cpf_valido, email_valido, somente_digitos


class Cliente(db.Model):
    __tablename__ = "cliente"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, index=True)
    tipo_pessoa = db.Column(db.Enum("F", "J", name="tipo_pessoa"), nullable=False)
    cpf_cnpj = db.Column(db.String(14), nullable=False, unique=True)
    inscricao_estadual = db.Column(db.String(20))
    propriedade = db.Column(db.String(120))
    cidade = db.Column(db.String(80), nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    pedidos = db.relationship("Pedido", back_populates="cliente")

    def preencher(self, dados: dict) -> list[str]:
        """Copia os dados do formulário e devolve a lista de erros (RN01)."""
        erros = []
        self.nome = (dados.get("nome") or "").strip()
        self.tipo_pessoa = dados.get("tipo_pessoa") or "F"
        self.cpf_cnpj = somente_digitos(dados.get("cpf_cnpj"))
        self.inscricao_estadual = (dados.get("inscricao_estadual") or "").strip() or None
        self.propriedade = (dados.get("propriedade") or "").strip() or None
        self.cidade = (dados.get("cidade") or "").strip()
        self.uf = (dados.get("uf") or "").upper()
        self.telefone = (dados.get("telefone") or "").strip() or None
        self.email = (dados.get("email") or "").strip().lower() or None

        if len(self.nome) < 3:
            erros.append("Informe o nome do cliente (mínimo 3 letras).")
        if self.tipo_pessoa == "F" and not cpf_valido(self.cpf_cnpj):
            erros.append("CPF inválido.")
        if self.tipo_pessoa == "J" and not cnpj_valido(self.cpf_cnpj):
            erros.append("CNPJ inválido.")
        if not self.cidade:
            erros.append("Informe a cidade.")
        if self.uf not in UFS:
            erros.append("Selecione a UF.")
        if self.email and not email_valido(self.email):
            erros.append("E-mail inválido.")

        with db.session.no_autoflush:
            duplicado = Cliente.query.filter(Cliente.cpf_cnpj == self.cpf_cnpj,
                                             Cliente.id != (self.id or 0)).first()
        if self.cpf_cnpj and duplicado:
            erros.append(f"Já existe um cliente com este documento: {duplicado.nome}.")
        return erros
