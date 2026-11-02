from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ..extensions import db


class RegraNegocioErro(Exception):
    """Erro de regra de negócio, mostrado ao usuário como mensagem."""


class Pedido(db.Model):
    __tablename__ = "pedido"

    STATUS = {
        "PENDENTE": "Pendente de faturamento",
        "FATURADO": "Faturado",
        "ENTREGUE": "Entregue",
        "CANCELADO": "Cancelado",
    }
    # RN04 - fluxo permitido de status
    TRANSICOES = {
        "PENDENTE": ("FATURADO", "CANCELADO"),
        "FATURADO": ("ENTREGUE",),
        "ENTREGUE": (),
        "CANCELADO": (),
    }

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)
    vendedor_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    data_pedido = db.Column(db.Date, nullable=False, default=date.today)
    data_prevista_entrega = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("PENDENTE", "FATURADO", "ENTREGUE", "CANCELADO",
                               name="status_pedido"), nullable=False, default="PENDENTE")
    valor_total = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    observacao = db.Column(db.String(500))
    numero_nf = db.Column(db.String(20), unique=True)
    data_faturamento = db.Column(db.Date)
    data_entrega = db.Column(db.Date)

    cliente = db.relationship("Cliente", back_populates="pedidos")
    vendedor = db.relationship("Usuario")
    itens = db.relationship("ItemPedido", back_populates="pedido",
                            cascade="all, delete-orphan", order_by="ItemPedido.id")
    historico = db.relationship("HistoricoStatus", back_populates="pedido",
                                cascade="all, delete-orphan",
                                order_by="HistoricoStatus.data_hora")

    # ------------------------------------------------------------------
    @property
    def numero(self) -> str:
        return f"PV-{self.id:05d}" if self.id else "Novo"

    @property
    def status_nome(self) -> str:
        return self.STATUS.get(self.status, self.status)

    @property
    def atrasado(self) -> bool:
        """RN06 - atrasado: ainda não entregue/cancelado e data prevista já passou."""
        return (self.status in ("PENDENTE", "FATURADO")
                and self.data_prevista_entrega < date.today())

    @property
    def dias_atraso(self) -> int:
        return (date.today() - self.data_prevista_entrega).days if self.atrasado else 0

    @property
    def editavel(self) -> bool:
        """RN03 - só pedidos pendentes podem ser alterados."""
        return self.status == "PENDENTE"

    # ------------------------------------------------------------------
    def preencher(self, dados: dict, itens: list[tuple]) -> list[str]:
        """Preenche cabeçalho e itens do pedido. `itens` = [(produto_id, quantidade), ...]"""
        from .cliente import Cliente
        from .produto import Produto

        erros = []
        if self.id and not self.editavel:
            return ["Este pedido não pode mais ser alterado (já foi faturado ou cancelado)."]

        try:
            self.cliente_id = int(dados.get("cliente_id") or 0)
        except ValueError:
            self.cliente_id = 0
        cliente = db.session.get(Cliente, self.cliente_id) if self.cliente_id else None
        if not cliente or not cliente.ativo:
            erros.append("Selecione um cliente ativo.")

        self.data_pedido = _ler_data(dados.get("data_pedido")) or date.today()
        self.data_prevista_entrega = _ler_data(dados.get("data_prevista_entrega"))
        if not self.data_prevista_entrega:
            erros.append("Informe a data prevista de entrega.")
        elif self.data_prevista_entrega < self.data_pedido:
            erros.append("A data prevista de entrega não pode ser anterior à data do pedido.")
        self.observacao = (dados.get("observacao") or "").strip()[:500] or None

        # RN02 - pedido precisa ter ao menos um item válido
        novos_itens = []
        for produto_id, quantidade in itens:
            if not produto_id and not quantidade:
                continue
            try:
                qtd = Decimal(str(quantidade).replace(",", "."))
            except (InvalidOperation, ValueError):
                qtd = Decimal("0")
            produto = db.session.get(Produto, int(produto_id)) if str(produto_id).isdigit() else None
            if not produto or not produto.ativo:
                erros.append("Há um item com produto inválido ou inativo.")
                continue
            if qtd <= 0:
                erros.append(f"Quantidade inválida para {produto.descricao}.")
                continue
            # RN05 - preço registrado no momento do lançamento
            preco = Decimal(str(produto.preco_unitario))
            novos_itens.append(ItemPedido(produto=produto, quantidade=qtd, preco_unitario=preco,
                                          subtotal=(qtd * preco).quantize(Decimal("0.01"))))
        if not novos_itens and not erros:
            erros.append("Adicione pelo menos um produto ao pedido.")

        if not erros:
            self.itens.clear()
            self.itens.extend(novos_itens)
            self.recalcular_total()
        return erros

    def recalcular_total(self):
        self.valor_total = sum((i.subtotal for i in self.itens), Decimal("0"))

    def alterar_status(self, novo: str, usuario, numero_nf: str = "", observacao: str = ""):
        """RN04/RN07/RN08 - muda o status validando fluxo, permissão e nota fiscal."""
        if novo not in self.TRANSICOES.get(self.status, ()):
            raise RegraNegocioErro(
                f"Não é possível passar de '{self.status_nome}' para '{self.STATUS.get(novo, novo)}'.")

        acao = {"FATURADO": "faturar_pedido", "ENTREGUE": "entregar_pedido",
                "CANCELADO": "cancelar_pedido"}[novo]
        if not usuario.pode(acao):
            raise RegraNegocioErro("Seu perfil não tem permissão para esta ação.")

        hoje = date.today()
        if novo == "FATURADO":
            numero_nf = (numero_nf or "").strip()
            if not numero_nf:
                raise RegraNegocioErro("Informe o número da nota fiscal para faturar.")
            existe = Pedido.query.filter(Pedido.numero_nf == numero_nf, Pedido.id != self.id).first()
            if existe:
                raise RegraNegocioErro(f"A NF {numero_nf} já foi usada no pedido {existe.numero}.")
            self.numero_nf = numero_nf
            self.data_faturamento = hoje
        elif novo == "ENTREGUE":
            self.data_entrega = hoje
        elif novo == "CANCELADO" and not (observacao or "").strip():
            raise RegraNegocioErro("Informe o motivo do cancelamento.")

        self.historico.append(HistoricoStatus(usuario_id=usuario.id, status_anterior=self.status,
                                              status_novo=novo, observacao=(observacao or "").strip() or None))
        self.status = novo


class ItemPedido(db.Model):
    __tablename__ = "item_pedido"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    quantidade = db.Column(db.Numeric(12, 3), nullable=False)
    preco_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(14, 2), nullable=False)

    pedido = db.relationship("Pedido", back_populates="itens")
    produto = db.relationship("Produto")


class HistoricoStatus(db.Model):
    __tablename__ = "historico_status"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    status_anterior = db.Column(db.String(20))
    status_novo = db.Column(db.String(20), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.now)
    observacao = db.Column(db.String(255))

    pedido = db.relationship("Pedido", back_populates="historico")
    usuario = db.relationship("Usuario")


def _ler_data(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date() if texto else None
    except ValueError:
        return None
