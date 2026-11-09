"""Consultas agregadas do relatório de vendas. Devolve apenas dados; as regras ficam no Service."""


class RelatorioModel:
    def total_pedidos(self, conn):
        return conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    def faturamento(self, conn):
        """Soma dos totais dos pedidos; None quando não há pedidos."""
        return conn.execute("SELECT SUM(total) FROM pedidos").fetchone()[0]

    def contar_por_status(self, conn, status):
        return conn.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", (status,)).fetchone()[0]
