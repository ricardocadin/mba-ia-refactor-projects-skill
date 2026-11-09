"""Validações reutilizadas pelos validators de cada domínio."""
from src.exceptions.errors import ValidationError


def exigir_objeto(dados):
    """O corpo da requisição precisa ser um objeto JSON não vazio."""
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    return dados


def eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)
