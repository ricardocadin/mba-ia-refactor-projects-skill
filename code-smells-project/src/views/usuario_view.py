"""Formatação de saída de usuários. O campo da senha nunca é exposto."""


def usuario_to_dict(usuario):
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
        "criado_em": usuario["criado_em"],
    }


def usuarios_to_list(usuarios):
    return [usuario_to_dict(u) for u in usuarios]


def login_to_dict(usuario):
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
    }
