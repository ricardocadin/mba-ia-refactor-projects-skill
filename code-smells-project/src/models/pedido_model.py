"""Acesso a dados de pedidos e itens. Consultas parametrizadas, sem commit (a transação é do Service)."""
from src.constants.pedido import PRODUTO_DESCONHECIDO, StatusPedido


class PedidoModel:
    def criar(self, conn, usuario_id, total):
        cursor = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, StatusPedido.PENDENTE, total),
        )
        return cursor.lastrowid

    def adicionar_item(self, conn, pedido_id, produto_id, quantidade, preco_unitario):
        conn.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, produto_id, quantidade, preco_unitario),
        )

    def buscar_por_id(self, conn, pedido_id):
        row = conn.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        return dict(row) if row else None

    def listar_itens(self, conn, pedido_id):
        rows = conn.execute(
            "SELECT produto_id, quantidade FROM itens_pedido WHERE pedido_id = ? ORDER BY id", (pedido_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def atualizar_status(self, conn, pedido_id, status):
        conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def listar_com_itens(self, conn, usuario_id=None):
        """Pedidos com itens e nome do produto em uma única consulta (sem N+1)."""
        query = (
            "SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em, "
            "i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario, "
            "pr.id AS produto_existente, pr.nome AS produto_nome "
            "FROM pedidos p "
            "LEFT JOIN itens_pedido i ON i.pedido_id = p.id "
            "LEFT JOIN produtos pr ON pr.id = i.produto_id"
        )
        params = []
        if usuario_id is not None:
            query += " WHERE p.usuario_id = ?"
            params.append(usuario_id)
        query += " ORDER BY p.id, i.id"

        pedidos = {}
        for row in conn.execute(query, params).fetchall():
            pedido = pedidos.setdefault(row["id"], {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            })
            if row["item_id"] is not None:
                pedido["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] if row["produto_existente"] is not None else PRODUTO_DESCONHECIDO,
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return list(pedidos.values())
