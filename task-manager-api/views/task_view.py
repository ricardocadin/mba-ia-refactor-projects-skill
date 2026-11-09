def task_to_dict(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': str(task.created_at),
        'updated_at': str(task.updated_at),
        'due_date': str(task.due_date) if task.due_date else None,
        'tags': task.tags.split(',') if task.tags else [],
    }


def task_with_overdue(task):
    data = task_to_dict(task)
    data['overdue'] = task.is_overdue()
    return data


def task_with_relations(task):
    data = task_with_overdue(task)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def task_summary(task):
    """Formato resumido usado em GET /users/<id>/tasks."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': str(task.due_date) if task.due_date else None,
        'overdue': task.is_overdue(),
    }
