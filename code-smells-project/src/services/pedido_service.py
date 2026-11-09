"""Casos de uso de pedidos. O Service define a fronteira da transação: tudo ou nada."""
from src.constants.pedido import StatusPedido
from src.exceptions.errors import ValidationError


class PedidoService:
    def __init__(self, database, pedido_model, produto_model, usuario_model, notificacoes):
        self._db = database
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._notificacoes = notificacoes

    def listar(self, usuario_id=None):
        with self._db.transaction() as conn:
            return self._pedidos.listar_com_itens(conn, usuario_id)

    def criar(self, usuario_id, itens):
        # commit no fim do bloco; qualquer exceção desfaz todas as escritas (rollback)
        with self._db.transaction() as conn:
            if self._usuarios.buscar_por_id(conn, usuario_id) is None:
                raise ValidationError("Usuario não encontrado", sucesso=False)
            total = 0
            linhas = []
            for item in itens:
                produto = self._produtos.buscar_por_id(conn, item["produto_id"])
                if produto is None:
                    raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado", sucesso=False)
                if produto["estoque"] < item["quantidade"]:
                    raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)
                total = total + (produto["preco"] * item["quantidade"])
                linhas.append((produto, item["quantidade"]))

            pedido_id = self._pedidos.criar(conn, usuario_id, total)
            for produto, quantidade in linhas:
                self._pedidos.adicionar_item(conn, pedido_id, produto["id"], quantidade, produto["preco"])
                if not self._produtos.baixar_estoque(conn, produto["id"], quantidade):
                    raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)

        self._notificacoes.pedido_criado(pedido_id, usuario_id)  # somente depois do commit
        return {"pedido_id": pedido_id, "total": total}

    def atualizar_status(self, pedido_id, novo_status):
        with self._db.transaction() as conn:
            pedido = self._pedidos.buscar_por_id(conn, pedido_id)
            self._pedidos.atualizar_status(conn, pedido_id, novo_status)
            # Cancelamento devolve o estoque na mesma transação, uma única vez (idempotente)
            if novo_status == StatusPedido.CANCELADO and pedido and pedido["status"] != StatusPedido.CANCELADO:
                for item in self._pedidos.listar_itens(conn, pedido_id):
                    self._produtos.devolver_estoque(conn, item["produto_id"], item["quantidade"])

        if novo_status == StatusPedido.APROVADO:
            self._notificacoes.pedido_aprovado(pedido_id)
        if novo_status == StatusPedido.CANCELADO:
            self._notificacoes.pedido_cancelado(pedido_id)
