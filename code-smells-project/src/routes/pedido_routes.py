"""Rotas de pedidos e do relatório de vendas."""
from flask import Blueprint


def build_pedido_blueprint(pedido_controller, relatorio_controller):
    bp = Blueprint("pedidos", __name__)
    bp.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar, methods=["POST"])
    bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos, methods=["GET"])
    bp.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
        pedido_controller.listar_por_usuario, methods=["GET"],
    )
    bp.add_url_rule(
        "/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
        pedido_controller.atualizar_status, methods=["PUT"],
    )
    bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorio_controller.vendas, methods=["GET"])
    return bp
