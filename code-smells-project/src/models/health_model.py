"""Consultas de contagem usadas pelo health check."""


class HealthModel:
    def contar_registros(self, conn):
        conn.execute("SELECT 1")
        return {
            "produtos": conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
            "usuarios": conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
            "pedidos": conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
        }
