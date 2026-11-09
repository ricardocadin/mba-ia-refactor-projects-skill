"""Validação de entrada do domínio de pedidos."""
from src.constants.pedido import STATUS_VALIDOS
from src.exceptions.errors import ValidationError
from src.validators.common import eh_inteiro, exigir_objeto


def validar_pedido_criacao(dados):
    exigir_objeto(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not eh_inteiro(usuario_id):
        raise ValidationError("Usuario ID deve ser inteiro")
    if not isinstance(itens, list):
        raise ValidationError("Itens deve ser uma lista")
    for item in itens:
        if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
            raise ValidationError("Cada item deve ter produto_id e quantidade")
        if not eh_inteiro(item["produto_id"]) or not eh_inteiro(item["quantidade"]):
            raise ValidationError("produto_id e quantidade devem ser inteiros")
        if item["quantidade"] <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
    return {"usuario_id": usuario_id, "itens": itens}


def validar_status(dados):
    if not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    status = dados.get("status", "")
    if status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return status
