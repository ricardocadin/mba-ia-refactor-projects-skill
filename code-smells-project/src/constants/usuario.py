"""Constantes do domínio de usuários."""

TIPO_CLIENTE = "cliente"
TIPO_ADMIN = "admin"

# Prefixos dos hashes gerados por werkzeug.security (usados para detectar senhas legadas em texto puro)
PREFIXOS_HASH_SENHA = ("scrypt:", "pbkdf2:")
