"""Validação de entrada do domínio de produtos (compartilhada entre criação e atualização)."""
from src.constants.produto import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_MAX_LEN, NOME_MIN_LEN
from src.exceptions.errors import ValidationError
from src.validators.common import eh_numero, exigir_objeto

_OBRIGATORIOS = (
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
)


def _validar_campos_base(dados):
    exigir_objeto(dados)
    for campo, mensagem in _OBRIGATORIOS:
        if campo not in dados:
            raise ValidationError(mensagem)

    preco, estoque = dados["preco"], dados["estoque"]
    if not eh_numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not eh_numero(estoque):
        raise ValidationError("Estoque deve ser numérico")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)
    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not isinstance(categoria, str):
        raise ValidationError("Categoria deve ser texto")
    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_produto_criacao(dados):
    produto = _validar_campos_base(dados)
    if len(produto["nome"]) < NOME_MIN_LEN:
        raise ValidationError("Nome muito curto")
    if len(produto["nome"]) > NOME_MAX_LEN:
        raise ValidationError("Nome muito longo")
    if produto["categoria"] not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))
    return produto


def validar_produto_atualizacao(dados):
    # Mantém o comportamento original: a atualização não valida tamanho do nome nem categoria
    return _validar_campos_base(dados)


def validar_filtros_busca(args):
    termo = args.get("q", "")
    categoria = args.get("categoria", None)
    preco_min = args.get("preco_min", None)
    preco_max = args.get("preco_max", None)
    return {
        "termo": termo,
        "categoria": categoria,
        "preco_min": _para_float(preco_min, "preco_min"),
        "preco_max": _para_float(preco_max, "preco_max"),
    }


def _para_float(valor, nome):
    if not valor:
        return valor
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(nome + " deve ser numérico")
