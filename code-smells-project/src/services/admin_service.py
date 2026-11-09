"""Operações administrativas."""
import logging

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, database, admin_model):
        self._db = database
        self._model = admin_model

    def resetar_banco(self):
        with self._db.transaction() as conn:  # as quatro limpezas são atômicas
            self._model.limpar_tabelas(conn)
        logger.warning("Banco de dados resetado")
