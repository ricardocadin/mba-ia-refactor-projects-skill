"""Rotas administrativas: exigem token de usuário com perfil admin."""
from flask import Blueprint

from src.constants.usuario import TIPO_ADMIN
from src.middlewares.auth_middleware import exigir_perfil


def build_admin_blueprint(controller, auth_service):
    bp = Blueprint("admin", __name__)
    somente_admin = exigir_perfil(auth_service, TIPO_ADMIN)
    bp.add_url_rule("/admin/reset-db", "reset_database", somente_admin(controller.resetar_banco), methods=["POST"])
    return bp
