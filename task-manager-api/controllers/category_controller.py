from flask import jsonify, request

from exceptions.errors import ValidationError
from validators.category_validator import validate_category_update_body, validate_new_category
from views.category_view import category_to_dict, category_with_task_count

INVALID_DATA_MESSAGE = 'Dados inválidos'


class CategoryController:
    def __init__(self, service):
        self._service = service

    def index(self):
        categories = self._service.list_categories()
        return jsonify([category_with_task_count(category, count) for category, count in categories]), 200

    def create(self):
        data = request.get_json()
        if not data:
            raise ValidationError(INVALID_DATA_MESSAGE)
        category = self._service.create_category(validate_new_category(data))
        return jsonify(category_to_dict(category)), 201

    def update(self, category_id):
        category = self._service.get_category(category_id)
        data = request.get_json()
        validate_category_update_body(data)
        category = self._service.update_category(category, data)
        return jsonify(category_to_dict(category)), 200

    def destroy(self, category_id):
        self._service.delete_category(category_id)
        return jsonify({'message': 'Categoria deletada'}), 200
