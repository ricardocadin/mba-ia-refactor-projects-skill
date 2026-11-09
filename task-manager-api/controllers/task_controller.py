from flask import jsonify, request

from exceptions.errors import ValidationError
from validators.task_validator import validate_new_task, validate_task_update
from views.task_view import task_to_dict, task_with_overdue, task_with_relations

INVALID_DATA_MESSAGE = 'Dados inválidos'


class TaskController:
    def __init__(self, service):
        self._service = service

    def index(self):
        tasks = self._service.list_tasks()
        return jsonify([task_with_relations(task) for task in tasks]), 200

    def show(self, task_id):
        task = self._service.get_task(task_id)
        return jsonify(task_with_overdue(task)), 200

    def create(self):
        data = request.get_json()
        if not data:
            raise ValidationError(INVALID_DATA_MESSAGE)
        task = self._service.create_task(validate_new_task(data))
        return jsonify(task_to_dict(task)), 201

    def update(self, task_id):
        task = self._service.get_task(task_id)
        data = request.get_json()
        if not data:
            raise ValidationError(INVALID_DATA_MESSAGE)
        validate_task_update(data)
        task = self._service.update_task(task, data)
        return jsonify(task_to_dict(task)), 200

    def destroy(self, task_id):
        self._service.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    def search(self):
        tasks = self._service.search(
            request.args.get('q', ''),
            request.args.get('status', ''),
            request.args.get('priority', ''),
            request.args.get('user_id', ''),
        )
        return jsonify([task_to_dict(task) for task in tasks]), 200

    def stats(self):
        return jsonify(self._service.stats()), 200
