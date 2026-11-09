"""Autenticação e autorização por perfil (token Bearer)."""
from functools import wraps

from flask import request

from src.exceptions.errors import ForbiddenError, UnauthorizedError

_PREFIXO_BEARER = "Bearer "


def exigir_perfil(auth_service, perfil):
    """Decorator que exige um token válido cujo perfil (`tipo`) seja o informado."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            cabecalho = request.headers.get("Authorization", "")
            if not cabecalho.startswith(_PREFIXO_BEARER):
                raise UnauthorizedError("Token ausente")
            payload = auth_service.validar_token(cabecalho[len(_PREFIXO_BEARER):])
            if payload.get("tipo") != perfil:
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)

        return wrapper

    return decorator
