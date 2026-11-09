import logging
import os
import secrets

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Unico modulo que le o ambiente. Os demais recebem os valores por injecao."""

    def __init__(self, env=None):
        if env is None:
            load_dotenv()
            env = os.environ

        self.DEBUG = env.get('APP_DEBUG', '0') == '1'
        self.SECRET_KEY = env.get('SECRET_KEY')
        self.DATABASE_URL = env.get('DATABASE_URL', 'sqlite:///tasks.db')
        self.HOST = env.get('HOST', '127.0.0.1')
        self.PORT = int(env.get('PORT', '5000'))
        self.TOKEN_MAX_AGE = int(env.get('TOKEN_MAX_AGE', '3600'))
        self.LOG_LEVEL = env.get('LOG_LEVEL', 'INFO')
        # Origens de navegador permitidas pelo CORS, separadas por virgula. Vazio = nenhuma.
        self.CORS_ORIGINS = [o.strip() for o in env.get('CORS_ORIGINS', '').split(',') if o.strip()]

        if not self.SECRET_KEY:
            if not self.DEBUG:
                raise RuntimeError(
                    'SECRET_KEY nao definida no ambiente (defina SECRET_KEY ou APP_DEBUG=1 para desenvolvimento)'
                )
            # So em desenvolvimento (APP_DEBUG=1): chave aleatoria por processo, sem literal no codigo.
            # Os tokens emitidos nao sobrevivem a um reinicio.
            self.SECRET_KEY = secrets.token_hex(32)
