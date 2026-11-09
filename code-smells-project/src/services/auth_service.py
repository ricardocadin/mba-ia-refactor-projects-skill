"""Emissão e validação de tokens assinados com expiração."""
from itsdangerous import BadSignature, URLSafeTimedSerializer

from src.exceptions.errors import UnauthorizedError

_SALT = "auth"


class AuthService:
    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=_SALT)
        self._max_age = max_age

    def emitir_token(self, usuario):
        return self._serializer.dumps({"id": usuario["id"], "tipo": usuario["tipo"]})

    def validar_token(self, token):
        try:
            return self._serializer.loads(token, max_age=self._max_age)
        except BadSignature:  # inclui token expirado
            raise UnauthorizedError("Token inválido ou expirado")
