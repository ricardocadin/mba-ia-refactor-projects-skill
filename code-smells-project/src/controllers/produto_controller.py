"""Controller de produtos: lê a entrada, chama o Service e escolhe a resposta HTTP."""
from flask import jsonify, request

from src.exceptions.errors import NotFoundError
from src.validators.produto_validator import (
    validar_filtros_busca,
    validar_produto_atualizacao,
    validar_produto_criacao,
)
from src.views.produto_view import produto_to_dict, produtos_to_list


class ProdutoController:
    def __init__(self, service):
        self._service = service

    def listar(self):
        produtos = self._service.listar()
        return jsonify({"dados": produtos_to_list(produtos), "sucesso": True}), 200

    def buscar(self, produto_id):
        produto = self._service.buscar(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado", sucesso=False)
        return jsonify({"dados": produto_to_dict(produto), "sucesso": True}), 200

    def criar(self):
        dados = validar_produto_criacao(request.get_json(silent=True))
        produto_id = self._service.criar(dados)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        if not self._service.buscar(produto_id):
            raise NotFoundError("Produto não encontrado")
        dados = validar_produto_atualizacao(request.get_json(silent=True))
        self._service.atualizar(produto_id, dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        if not self._service.buscar(produto_id):
            raise NotFoundError("Produto não encontrado")
        self._service.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    def pesquisar(self):
        filtros = validar_filtros_busca(request.args)
        resultados = self._service.pesquisar(**filtros)
        return jsonify({"dados": produtos_to_list(resultados), "total": len(resultados), "sucesso": True}), 200
