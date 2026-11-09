from datetime import datetime, timedelta

from constants.report import RECENT_DAYS
from constants.task import (
    HIGH_PRIORITY_MAX,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from exceptions.errors import NotFoundError
from services.metrics import completion_rate


class ReportService:
    def __init__(self, task_model, user_model, category_model):
        self._tasks = task_model
        self._users = user_model
        self._categories = category_model

    def summary(self):
        now = datetime.utcnow()
        by_status = self._tasks.count_by_status()

        overdue = [
            {'id': task.id, 'title': task.title, 'due_date': task.due_date, 'days_overdue': (now - task.due_date).days}
            for task in self._tasks.list_all()
            if task.is_overdue()
        ]

        since = now - timedelta(days=RECENT_DAYS)
        counts_by_user = self._tasks.count_by_user()
        user_stats = []
        for user in self._users.list_all():
            total, completed = counts_by_user.get(user.id, (0, 0))
            user_stats.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': completion_rate(completed, total),
            })

        return {
            'generated_at': now,
            'total_tasks': self._tasks.count(),
            'total_users': self._users.count(),
            'total_categories': self._categories.count(),
            'by_status': {
                STATUS_PENDING: by_status.get(STATUS_PENDING, 0),
                STATUS_IN_PROGRESS: by_status.get(STATUS_IN_PROGRESS, 0),
                STATUS_DONE: by_status.get(STATUS_DONE, 0),
                STATUS_CANCELLED: by_status.get(STATUS_CANCELLED, 0),
            },
            'by_priority': self._tasks.count_by_priority(),
            'overdue': overdue,
            'created_recently': self._tasks.count_created_since(since),
            'completed_recently': self._tasks.count_done_updated_since(since),
            'user_stats': user_stats,
        }

    def user_report(self, user_id):
        user = self._users.find_by_id(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = self._tasks.list_by_user(user_id)
        total = len(tasks)
        done = sum(1 for task in tasks if task.status == STATUS_DONE)

        statistics = {
            'total_tasks': total,
            'done': done,
            'pending': sum(1 for task in tasks if task.status == STATUS_PENDING),
            'in_progress': sum(1 for task in tasks if task.status == STATUS_IN_PROGRESS),
            'cancelled': sum(1 for task in tasks if task.status == STATUS_CANCELLED),
            'overdue': sum(1 for task in tasks if task.is_overdue()),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': completion_rate(done, total),
        }
        return user, statistics
