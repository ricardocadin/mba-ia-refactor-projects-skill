def completion_rate(completed, total):
    if total > 0:
        return round((completed / total) * 100, 2)
    return 0
