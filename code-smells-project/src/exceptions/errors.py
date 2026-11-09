"""Exceções de domínio. O handler global (middlewares/error_middleware.py) as converte em resposta HTTP."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message, sucesso=None):
        super().__init__(message)
        self.message = message
        # Quando informado, o corpo de erro inclui "sucesso" (preserva o contrato original de alguns endpoints)
        self.sucesso = sucesso


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409
