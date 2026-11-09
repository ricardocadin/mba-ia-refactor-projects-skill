from views.task_view import task_to_dict


def user_to_dict(user):
    """Representacao publica do usuario: nunca inclui a senha nem o hash."""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
    }


def user_with_task_count(user, task_count):
    data = user_to_dict(user)
    data['task_count'] = task_count
    return data


def user_with_tasks(user, tasks):
    data = user_to_dict(user)
    data['tasks'] = [task_to_dict(task) for task in tasks]
    return data
