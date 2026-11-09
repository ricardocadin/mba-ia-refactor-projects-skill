from itsdangerous import BadSignature, URLSafeTimedSerializer

from exceptions.errors import UnauthorizedError

TOKEN_SALT = 'auth'


class AuthService:
    """Emite e valida tokens assinados (a chave e a validade vem da Config, via composition root)."""

    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=TOKEN_SALT)
        self._max_age = max_age

    def issue_token(self, user):
        return self._serializer.dumps({'id': user.id, 'role': user.role})

    def verify_token(self, token):
        try:
            return self._serializer.loads(token, max_age=self._max_age)
        except BadSignature:
            raise UnauthorizedError('Token inválido ou expirado')
