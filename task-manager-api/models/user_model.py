from database import db
from models.user import User


class UserModel:
    """Acesso a dados de User. Sem estado e sem commit (a transacao e do service)."""

    def find_by_id(self, user_id):
        return db.session.get(User, user_id)

    def find_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def list_all(self):
        return User.query.all()

    def count(self):
        return User.query.count()

    def add(self, user):
        db.session.add(user)

    def delete(self, user):
        db.session.delete(user)
