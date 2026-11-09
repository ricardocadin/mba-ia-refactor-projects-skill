"""Constantes do domínio de pedidos."""


class StatusPedido:
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


PRODUTO_DESCONHECIDO = "Desconhecido"

STATUS_VALIDOS = (
    StatusPedido.PENDENTE,
    StatusPedido.APROVADO,
    StatusPedido.ENVIADO,
    StatusPedido.ENTREGUE,
    StatusPedido.CANCELADO,
)
