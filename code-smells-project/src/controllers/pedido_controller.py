"""Controller de pedidos."""
from flask import jsonify, request

from src.validators.pedido_validator import validar_pedido_criacao, validar_status
from src.views.pedido_view import pedidos_to_list


class PedidoController:
    def __init__(self, service):
        self._service = service

    def criar(self):
        dados = validar_pedido_criacao(request.get_json(silent=True))
        resultado = self._service.criar(**dados)
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    def listar_todos(self):
        return jsonify({"dados": pedidos_to_list(self._service.listar()), "sucesso": True}), 200

    def listar_por_usuario(self, usuario_id):
        return jsonify({"dados": pedidos_to_list(self._service.listar(usuario_id)), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        novo_status = validar_status(request.get_json(silent=True))
        self._service.atualizar_status(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
