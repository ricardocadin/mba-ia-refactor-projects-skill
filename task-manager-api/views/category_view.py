def category_to_dict(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }


def category_with_task_count(category, task_count):
    data = category_to_dict(category)
    data['task_count'] = task_count
    return data
