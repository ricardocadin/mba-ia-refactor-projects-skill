from functools import wraps

from flask import request

from exceptions.errors import ForbiddenError, UnauthorizedError

BEARER_PREFIX = 'Bearer '


class AuthMiddleware:
    def __init__(self, auth_service):
        self._auth = auth_service

    def require(self, role=None):
        """Exige token valido; com `role`, exige tambem essa role."""
        def decorator(view):
            @wraps(view)
            def wrapper(*args, **kwargs):
                header = request.headers.get('Authorization', '')
                if not header.startswith(BEARER_PREFIX):
                    raise UnauthorizedError('Token ausente')
                payload = self._auth.verify_token(header[len(BEARER_PREFIX):])
                if role and payload.get('role') != role:
                    raise ForbiddenError('Acesso negado')
                return view(*args, **kwargs)
            return wrapper
        return decorator
