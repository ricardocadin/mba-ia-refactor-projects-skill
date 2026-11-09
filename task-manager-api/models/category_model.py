from database import db
from models.category import Category


class CategoryModel:
    """Acesso a dados de Category. Sem estado e sem commit (a transacao e do service)."""

    def find_by_id(self, category_id):
        return db.session.get(Category, category_id)

    def list_all(self):
        return Category.query.all()

    def count(self):
        return Category.query.count()

    def add(self, category):
        db.session.add(category)

    def delete(self, category):
        db.session.delete(category)
