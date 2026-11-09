"""Controller da raiz e do health check."""
from flask import jsonify

from src.views.health_view import health_to_dict, indice_to_dict


class HealthController:
    def __init__(self, service, versao, ambiente):
        self._service = service
        self._versao = versao
        self._ambiente = ambiente

    def index(self):
        return jsonify(indice_to_dict(self._versao))

    def health(self):
        contagens = self._service.contagens()
        return jsonify(health_to_dict(contagens, self._versao, self._ambiente)), 200
