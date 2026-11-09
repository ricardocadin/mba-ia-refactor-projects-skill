from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from constants.task import STATUS_DONE
from database import db
from models.task import Task


class TaskModel:
    """Acesso a dados de Task. Sem estado e sem commit (a transacao e do service)."""

    def find_by_id(self, task_id):
        return db.session.get(Task, task_id)

    def list_all(self):
        return Task.query.order_by(Task.id).all()

    def list_all_with_relations(self):
        return (
            Task.query
            .options(joinedload(Task.user), joinedload(Task.category))
            .order_by(Task.id)
            .all()
        )

    def list_by_user(self, user_id):
        return Task.query.filter_by(user_id=user_id).all()

    def search(self, term='', status='', priority=None, user_id=None):
        query = Task.query
        if term:
            pattern = '%' + term + '%'
            query = query.filter(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        return query.all()

    def count(self):
        return Task.query.count()

    def count_by_status(self):
        rows = db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
        return {status: total for status, total in rows}

    def count_by_priority(self):
        rows = db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
        return {priority: total for priority, total in rows}

    def count_by_category(self):
        rows = db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all()
        return {category_id: total for category_id, total in rows}

    def count_by_user(self):
        """Devolve {user_id: (total, concluidas)} em uma unica consulta."""
        done = func.sum(case((Task.status == STATUS_DONE, 1), else_=0))
        rows = db.session.query(Task.user_id, func.count(Task.id), done).group_by(Task.user_id).all()
        return {user_id: (total, int(completed or 0)) for user_id, total, completed in rows}

    def count_created_since(self, moment):
        return Task.query.filter(Task.created_at >= moment).count()

    def count_done_updated_since(self, moment):
        return Task.query.filter(Task.status == STATUS_DONE, Task.updated_at >= moment).count()

    def add(self, task):
        db.session.add(task)

    def delete(self, task):
        db.session.delete(task)

    def delete_by_user(self, user_id):
        for task in self.list_by_user(user_id):
            db.session.delete(task)
