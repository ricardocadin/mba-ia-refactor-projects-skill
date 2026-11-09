"""Casos de uso de produtos."""
import logging

logger = logging.getLogger(__name__)


class ProdutoService:
    def __init__(self, database, produto_model):
        self._db = database
        self._model = produto_model

    def listar(self):
        with self._db.transaction() as conn:
            return self._model.listar_todos(conn)

    def buscar(self, produto_id):
        with self._db.transaction() as conn:
            return self._model.buscar_por_id(conn, produto_id)

    def pesquisar(self, termo, categoria=None, preco_min=None, preco_max=None):
        with self._db.transaction() as conn:
            return self._model.buscar(conn, termo, categoria, preco_min, preco_max)

    def criar(self, dados):
        with self._db.transaction() as conn:
            produto_id = self._model.criar(conn, **dados)
        logger.info("Produto criado: id=%s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        with self._db.transaction() as conn:
            self._model.atualizar(conn, produto_id, **dados)

    def deletar(self, produto_id):
        with self._db.transaction() as conn:
            self._model.deletar(conn, produto_id)
        logger.info("Produto deletado: id=%s", produto_id)
