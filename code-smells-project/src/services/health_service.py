"""Caso de uso do health check."""


class HealthService:
    def __init__(self, database, health_model):
        self._db = database
        self._model = health_model

    def contagens(self):
        with self._db.transaction() as conn:
            return self._model.contar_registros(conn)
