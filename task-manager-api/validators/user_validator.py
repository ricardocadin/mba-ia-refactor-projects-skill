import re

from constants.user import DEFAULT_ROLE, EMAIL_PATTERN, MIN_PASSWORD_LENGTH, USER_ROLES
from exceptions.errors import ValidationError


def validate_email_format(email):
    if not re.match(EMAIL_PATTERN, email):
        raise ValidationError('Email inválido')


def validate_password_length(password, message):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)


def validate_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')


def validate_new_user(data):
    """Valida o formato dos campos de criacao e devolve os valores para o service."""
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')

    validate_email_format(email)
    validate_password_length(password, 'Senha deve ter no mínimo %d caracteres' % MIN_PASSWORD_LENGTH)

    return {'name': name, 'email': email, 'password': password, 'role': role}


def validate_credentials(data):
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    return email, password
