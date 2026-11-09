"""Rotas da raiz e do health check."""
from flask import Blueprint


def build_health_blueprint(controller):
    bp = Blueprint("health", __name__)
    bp.add_url_rule("/", "index", controller.index, methods=["GET"])
    bp.add_url_rule("/health", "health_check", controller.health, methods=["GET"])
    return bp
