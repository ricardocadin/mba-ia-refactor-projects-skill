"""Formatação de saída de pedidos e do relatório de vendas (único ponto de arredondamento)."""
from src.constants.relatorio import CASAS_DECIMAIS


def pedido_to_dict(pedido):
    return {
        "id": pedido["id"],
        "usuario_id": pedido["usuario_id"],
        "status": pedido["status"],
        "total": pedido["total"],
        "criado_em": pedido["criado_em"],
        "itens": [
            {
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"],
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            }
            for item in pedido["itens"]
        ],
    }


def pedidos_to_list(pedidos):
    return [pedido_to_dict(p) for p in pedidos]


def relatorio_to_dict(relatorio):
    faturamento = relatorio["faturamento"]
    desconto = relatorio["desconto"]
    total_pedidos = relatorio["total_pedidos"]
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, CASAS_DECIMAIS),
        "desconto_aplicavel": round(desconto, CASAS_DECIMAIS),
        "faturamento_liquido": round(faturamento - desconto, CASAS_DECIMAIS),
        "pedidos_pendentes": relatorio["pendentes"],
        "pedidos_aprovados": relatorio["aprovados"],
        "pedidos_cancelados": relatorio["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, CASAS_DECIMAIS) if total_pedidos > 0 else 0,
    }
