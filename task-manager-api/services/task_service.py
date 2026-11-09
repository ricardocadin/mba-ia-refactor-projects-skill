import logging
from datetime import datetime

from constants.task import (
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from exceptions.errors import NotFoundError, PersistenceError
from models.task import Task
from models.transaction import transaction
from services.metrics import completion_rate
from validators.task_validator import (
    DUE_DATE_ERROR_ON_CREATE,
    DUE_DATE_ERROR_ON_UPDATE,
    normalize_tags,
    parse_due_date,
    parse_int_filter,
)

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, task_model, user_model, category_model):
        self._tasks = task_model
        self._users = user_model
        self._categories = category_model

    def list_tasks(self):
        return self._tasks.list_all_with_relations()

    def get_task(self, task_id):
        task = self._tasks.find_by_id(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def create_task(self, fields):
        self._ensure_user_exists(fields['user_id'])
        self._ensure_category_exists(fields['category_id'])

        task = Task()
        task.title = fields['title']
        task.description = fields['description']
        task.status = fields['status']
        task.priority = fields['priority']
        task.user_id = fields['user_id']
        task.category_id = fields['category_id']

        if fields['due_date']:
            task.due_date = parse_due_date(fields['due_date'], DUE_DATE_ERROR_ON_CREATE)
        if fields['tags']:
            task.tags = normalize_tags(fields['tags'])

        try:
            with transaction():
                self._tasks.add(task)
        except Exception as err:
            raise PersistenceError('Erro ao criar task') from err

        logger.info('Task criada: id=%s', task.id)
        return task

    def update_task(self, task, data):
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'priority' in data:
            task.priority = data['priority']

        if 'user_id' in data:
            self._ensure_user_exists(data['user_id'])
            task.user_id = data['user_id']

        if 'category_id' in data:
            self._ensure_category_exists(data['category_id'])
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                task.due_date = parse_due_date(data['due_date'], DUE_DATE_ERROR_ON_UPDATE)
            else:
                task.due_date = None

        if 'tags' in data:
            task.tags = normalize_tags(data['tags'])

        task.updated_at = datetime.utcnow()

        try:
            with transaction():
                pass
        except Exception as err:
            raise PersistenceError('Erro ao atualizar') from err

        logger.info('Task atualizada: id=%s', task.id)
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        try:
            with transaction():
                self._tasks.delete(task)
        except Exception as err:
            raise PersistenceError('Erro ao deletar') from err
        logger.info('Task deletada: id=%s', task_id)

    def search(self, term='', status='', priority='', user_id=''):
        priority_filter = parse_int_filter(priority, 'Prioridade inválida') if priority else None
        user_filter = parse_int_filter(user_id, 'user_id inválido') if user_id else None
        return self._tasks.search(term, status, priority_filter, user_filter)

    def stats(self):
        total = self._tasks.count()
        by_status = self._tasks.count_by_status()
        done = by_status.get(STATUS_DONE, 0)
        overdue = sum(1 for task in self._tasks.list_all() if task.is_overdue())

        return {
            'total': total,
            'pending': by_status.get(STATUS_PENDING, 0),
            'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
            'done': done,
            'cancelled': by_status.get(STATUS_CANCELLED, 0),
            'overdue': overdue,
            'completion_rate': completion_rate(done, total),
        }

    def _ensure_user_exists(self, user_id):
        if user_id and not self._users.find_by_id(user_id):
            raise NotFoundError('Usuário não encontrado')

    def _ensure_category_exists(self, category_id):
        if category_id and not self._categories.find_by_id(category_id):
            raise NotFoundError('Categoria não encontrada')
