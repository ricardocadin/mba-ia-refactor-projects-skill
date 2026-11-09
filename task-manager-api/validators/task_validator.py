from datetime import datetime

from constants.task import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    DUE_DATE_FORMAT,
    MAX_PRIORITY,
    MIN_PRIORITY,
    TASK_STATUSES,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
)
from exceptions.errors import ValidationError

DUE_DATE_ERROR_ON_CREATE = 'Formato de data inválido. Use YYYY-MM-DD'
DUE_DATE_ERROR_ON_UPDATE = 'Formato de data inválido'


def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título deve ser texto')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')


def validate_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError('Status inválido')


def validate_priority(priority):
    if not isinstance(priority, (int, float)):
        raise ValidationError('Prioridade deve ser numérica')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')


def parse_due_date(value, error_message):
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (ValueError, TypeError):
        raise ValidationError(error_message)


def normalize_tags(tags):
    if isinstance(tags, list):
        return ','.join(tags)
    return tags


def parse_int_filter(value, error_message):
    try:
        return int(value)
    except ValueError:
        raise ValidationError(error_message)


def validate_new_task(data):
    """Valida o formato dos campos de criacao e devolve os valores (com defaults) para o service."""
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    validate_title(title)

    fields = {
        'title': title,
        'description': data.get('description', ''),
        'status': data.get('status', DEFAULT_STATUS),
        'priority': data.get('priority', DEFAULT_PRIORITY),
        'user_id': data.get('user_id'),
        'category_id': data.get('category_id'),
        'due_date': data.get('due_date'),
        'tags': data.get('tags'),
    }
    validate_status(fields['status'])
    validate_priority(fields['priority'])
    return fields


def validate_task_update(data):
    """Valida o formato de title, status e priority quando presentes (na mesma ordem de antes)."""
    if 'title' in data:
        validate_title(data['title'])
    if 'status' in data:
        validate_status(data['status'])
    if 'priority' in data:
        validate_priority(data['priority'])
