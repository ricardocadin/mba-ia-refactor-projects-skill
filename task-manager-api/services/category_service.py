import logging

from exceptions.errors import NotFoundError, PersistenceError
from models.category import Category
from models.transaction import transaction

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, category_model, task_model):
        self._categories = category_model
        self._tasks = task_model

    def list_categories(self):
        """Devolve [(categoria, quantidade de tasks)] com uma unica consulta de contagem."""
        counts = self._tasks.count_by_category()
        return [(category, counts.get(category.id, 0)) for category in self._categories.list_all()]

    def get_category(self, category_id):
        category = self._categories.find_by_id(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category

    def create_category(self, fields):
        category = Category()
        category.name = fields['name']
        category.description = fields['description']
        category.color = fields['color']

        try:
            with transaction():
                self._categories.add(category)
        except Exception as err:
            raise PersistenceError('Erro ao criar categoria') from err

        logger.info('Categoria criada: id=%s', category.id)
        return category

    def update_category(self, category, data):
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']

        try:
            with transaction():
                pass
        except Exception as err:
            raise PersistenceError('Erro ao atualizar') from err

        return category

    def delete_category(self, category_id):
        category = self.get_category(category_id)
        try:
            with transaction():
                self._categories.delete(category)
        except Exception as err:
            raise PersistenceError('Erro ao deletar') from err
        logger.info('Categoria deletada: id=%s', category_id)
