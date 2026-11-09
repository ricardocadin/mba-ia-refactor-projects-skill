"""Controller de usuários e login."""
from flask import jsonify, request

from src.exceptions.errors import NotFoundError, UnauthorizedError
from src.validators.usuario_validator import validar_login, validar_usuario_criacao
from src.views.usuario_view import login_to_dict, usuario_to_dict, usuarios_to_list


class UsuarioController:
    def __init__(self, service, auth_service):
        self._service = service
        self._auth = auth_service

    def listar(self):
        return jsonify({"dados": usuarios_to_list(self._service.listar()), "sucesso": True}), 200

    def buscar(self, usuario_id):
        usuario = self._service.buscar(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return jsonify({"dados": usuario_to_dict(usuario), "sucesso": True}), 200

    def criar(self):
        dados = validar_usuario_criacao(request.get_json(silent=True))
        usuario_id = self._service.criar(**dados)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        credenciais = validar_login(request.get_json(silent=True))
        usuario = self._service.autenticar(**credenciais)
        if not usuario:
            raise UnauthorizedError("Email ou senha inválidos", sucesso=False)
        return jsonify({
            "dados": login_to_dict(usuario),
            "token": self._auth.emitir_token(usuario),
            "sucesso": True,
            "mensagem": "Login OK",
        }), 200
