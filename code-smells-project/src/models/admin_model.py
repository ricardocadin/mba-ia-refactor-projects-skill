"""Operações administrativas sobre o banco. Sem commit: a transação é do Service."""


class AdminModel:
    def limpar_tabelas(self, conn):
        conn.execute("DELETE FROM itens_pedido")
        conn.execute("DELETE FROM pedidos")
        conn.execute("DELETE FROM produtos")
        conn.execute("DELETE FROM usuarios")
