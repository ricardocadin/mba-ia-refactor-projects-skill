"""Regras do relatório de vendas (faixas de desconto)."""
from src.constants.pedido import StatusPedido
from src.constants.relatorio import FAIXAS_DESCONTO


def calcular_desconto(faturamento):
    """Faixa por faturamento, com comparação estrita (acima do limite)."""
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


class RelatorioService:
    def __init__(self, database, relatorio_model):
        self._db = database
        self._model = relatorio_model

    def vendas(self):
        with self._db.transaction() as conn:
            total_pedidos = self._model.total_pedidos(conn)
            faturamento = self._model.faturamento(conn)
            pendentes = self._model.contar_por_status(conn, StatusPedido.PENDENTE)
            aprovados = self._model.contar_por_status(conn, StatusPedido.APROVADO)
            cancelados = self._model.contar_por_status(conn, StatusPedido.CANCELADO)

        if faturamento is None:
            faturamento = 0
        return {
            "total_pedidos": total_pedidos,
            "faturamento": faturamento,
            "desconto": calcular_desconto(faturamento),
            "pendentes": pendentes,
            "aprovados": aprovados,
            "cancelados": cancelados,
        }
