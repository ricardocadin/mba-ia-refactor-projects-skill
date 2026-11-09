"""Controller do relatório de vendas."""
from flask import jsonify

from src.views.pedido_view import relatorio_to_dict


class RelatorioController:
    def __init__(self, service):
        self._service = service

    def vendas(self):
        return jsonify({"dados": relatorio_to_dict(self._service.vendas()), "sucesso": True}), 200
