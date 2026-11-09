from flask import jsonify, request

from exceptions.errors import ValidationError
from validators.user_validator import validate_credentials, validate_new_user
from views.task_view import task_summary
from views.user_view import user_to_dict, user_with_task_count, user_with_tasks

INVALID_DATA_MESSAGE = 'Dados inválidos'


class UserController:
    def __init__(self, service):
        self._service = service

    def index(self):
        users = self._service.list_users()
        return jsonify([user_with_task_count(user, count) for user, count in users]), 200

    def show(self, user_id):
        user = self._service.get_user(user_id)
        tasks = self._service.get_user_tasks(user_id)
        return jsonify(user_with_tasks(user, tasks)), 200

    def create(self):
        data = request.get_json()
        if not data:
            raise ValidationError(INVALID_DATA_MESSAGE)
        user = self._service.create_user(validate_new_user(data))
        return jsonify(user_to_dict(user)), 201

    def update(self, user_id):
        user = self._service.get_user(user_id)
        data = request.get_json()
        if not data:
            raise ValidationError(INVALID_DATA_MESSAGE)
        user = self._service.update_user(user, data)
        return jsonify(user_to_dict(user)), 200

    def destroy(self, user_id):
        self._service.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    def tasks(self, user_id):
        self._service.get_user(user_id)
        tasks = self._service.get_user_tasks(user_id)
        return jsonify([task_summary(task) for task in tasks]), 200

    def login(self):
        data = request.get_json()
        if not data:
            raise ValidationError(INVALID_DATA_MESSAGE)
        email, password = validate_credentials(data)
        user, token = self._service.login(email, password)
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user_to_dict(user),
            'token': token,
        }), 200
