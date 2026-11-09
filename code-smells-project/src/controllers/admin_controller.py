"""Controller das rotas administrativas (protegidas por perfil admin nas rotas)."""
from flask import jsonify


class AdminController:
    def __init__(self, service):
        self._service = service

    def resetar_banco(self):
        self._service.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
