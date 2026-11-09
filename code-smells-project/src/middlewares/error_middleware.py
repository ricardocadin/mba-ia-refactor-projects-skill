"""Handler global de erros: nenhum controller captura exceções genéricas."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.constants.aplicacao import MENSAGEM_ERRO_INTERNO
from src.exceptions.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        corpo = {"erro": err.message}
        if err.sucesso is not None:
            corpo["sucesso"] = err.sucesso
        return jsonify(corpo), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        logger.exception("Erro não tratado")  # o detalhe fica só no log
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500
