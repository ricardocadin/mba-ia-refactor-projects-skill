from constants.category import DEFAULT_COLOR
from exceptions.errors import ValidationError


def validate_new_category(data):
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    return {
        'name': name,
        'description': data.get('description', ''),
        'color': data.get('color', DEFAULT_COLOR),
    }


def validate_category_update_body(data):
    if not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
