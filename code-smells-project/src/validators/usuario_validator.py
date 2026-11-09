"""Validação de entrada do domínio de usuários."""
from src.exceptions.errors import ValidationError
from src.validators.common import exigir_objeto


def validar_usuario_criacao(dados):
    exigir_objeto(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not all(isinstance(v, str) for v in (nome, email, senha)):
        raise ValidationError("Nome, email e senha devem ser texto")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    if not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    if not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha devem ser texto")
    return {"email": email, "senha": senha}
