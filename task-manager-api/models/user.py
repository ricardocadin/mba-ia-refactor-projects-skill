import hashlib
import hmac
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from constants.user import DEFAULT_ROLE, PASSWORD_HASH_PREFIXES, ROLE_ADMIN
from database import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, plain_password):
        self.password = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        if self.has_legacy_password_hash():
            return hmac.compare_digest(self.password, _legacy_md5(plain_password))
        return check_password_hash(self.password, plain_password)

    def has_legacy_password_hash(self):
        """Hashes MD5 gravados antes da troca de algoritmo; sao regravados no primeiro login valido."""
        return not self.password.startswith(PASSWORD_HASH_PREFIXES)

    def is_admin(self):
        return self.role == ROLE_ADMIN


def _legacy_md5(plain_password):
    return hashlib.md5(plain_password.encode(), usedforsecurity=False).hexdigest()
