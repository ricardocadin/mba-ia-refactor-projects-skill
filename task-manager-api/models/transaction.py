from contextlib import contextmanager

from database import db


@contextmanager
def transaction():
    """Fronteira de transacao usada pelos services: commit no fim, rollback em qualquer erro."""
    try:
        yield
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
