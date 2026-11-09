import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from exceptions.errors import AppError

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = 'Erro interno'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        if err.status_code >= 500 and err.__cause__ is not None:
            logger.error('%s', err.message, exc_info=err.__cause__)
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        if isinstance(err, HTTPException):
            return err
        logger.exception('Erro nao tratado')
        return jsonify({'error': GENERIC_ERROR_MESSAGE}), 500
