from constants.report import PRIORITY_LABELS
from views.user_view import user_to_dict


def summary_to_dict(summary):
    by_priority = summary['by_priority']
    return {
        'generated_at': str(summary['generated_at']),
        'overview': {
            'total_tasks': summary['total_tasks'],
            'total_users': summary['total_users'],
            'total_categories': summary['total_categories'],
        },
        'tasks_by_status': summary['by_status'],
        'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(summary['overdue']),
            'tasks': [
                {
                    'id': item['id'],
                    'title': item['title'],
                    'due_date': str(item['due_date']),
                    'days_overdue': item['days_overdue'],
                }
                for item in summary['overdue']
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': summary['created_recently'],
            'tasks_completed_last_7_days': summary['completed_recently'],
        },
        'user_productivity': summary['user_stats'],
    }


def user_report_to_dict(user, statistics):
    public = user_to_dict(user)
    return {
        'user': {'id': public['id'], 'name': public['name'], 'email': public['email']},
        'statistics': statistics,
    }
