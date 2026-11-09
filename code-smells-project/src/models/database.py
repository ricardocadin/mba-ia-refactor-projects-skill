"""Acesso ao banco: uma conexão por unidade de trabalho (sem estado global)."""
import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, url):
        self._url = url

    @contextmanager
    def transaction(self):
        """Abre a conexão, faz commit ao final e rollback em qualquer exceção."""
        conn = sqlite3.connect(self._url)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
