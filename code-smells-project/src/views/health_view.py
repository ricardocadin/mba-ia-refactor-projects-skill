"""Formatação das respostas de raiz e health check. Nunca expõe segredos nem configuração interna."""


def indice_to_dict(versao):
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": versao,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }


def health_to_dict(contagens, versao, ambiente):
    return {
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": versao,
        "ambiente": ambiente,
    }
