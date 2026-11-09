"""Configuração da aplicação. Único módulo que lê variáveis de ambiente."""
import os
import secrets


class Config:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        self.DEBUG = env.get("APP_DEBUG", "0") == "1"
        self.SECRET_KEY = env.get("SECRET_KEY")
        self.DATABASE_URL = env.get("DATABASE_URL", "loja.db")
        self.HOST = env.get("HOST", "127.0.0.1")  # padrão seguro: apenas local
        self.PORT = int(env.get("PORT", "5000"))
        self.TOKEN_MAX_AGE = int(env.get("TOKEN_MAX_AGE", "3600"))  # segundos
        self.LOG_LEVEL = env.get("LOG_LEVEL", "INFO")
        self.ENVIRONMENT = env.get("APP_ENV", "producao")
        if not self.SECRET_KEY:
            if not self.DEBUG:
                raise RuntimeError(
                    "SECRET_KEY não definida no ambiente "
                    "(em desenvolvimento, use APP_DEBUG=1 para gerar uma chave temporária)"
                )
            self.SECRET_KEY = secrets.token_hex(32)  # só em desenvolvimento; muda a cada boot
