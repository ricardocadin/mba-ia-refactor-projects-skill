"""Formatação de saída de produtos (único ponto de montagem do dicionário de produto)."""


def produto_to_dict(produto):
    return {
        "id": produto["id"],
        "nome": produto["nome"],
        "descricao": produto["descricao"],
        "preco": produto["preco"],
        "estoque": produto["estoque"],
        "categoria": produto["categoria"],
        "ativo": produto["ativo"],
        "criado_em": produto["criado_em"],
    }


def produtos_to_list(produtos):
    return [produto_to_dict(p) for p in produtos]
