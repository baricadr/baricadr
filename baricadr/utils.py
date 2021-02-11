def get_celery_worker_status(app):
    i = app.control.inspect()
    availability = i.ping()
    # stats = i.stats()
    result = {
        'availability': availability,
        # 'stats': stats,
    }
    return result


def get_celery_tasks(app):
    i = app.control.inspect()
    active_tasks = _get_celery_task_ids(i.active())
    reserved_tasks = _get_celery_task_ids(i.reserved())
    scheduled_tasks = _get_celery_task_ids(i.scheduled())
    result = {
        'active_tasks': active_tasks,
        'reserved_tasks': reserved_tasks,
        'scheduled_tasks': scheduled_tasks
    }
    return result


def _get_celery_task_ids(full_dict):
    res = []
    for worker in full_dict:
        for task in full_dict[worker]:
            res.append(task['id'])

    return res


def celery_task_is_in_queue(celery, task_id):

    cel_tasks = get_celery_tasks(celery)

    return task_id in cel_tasks['active_tasks'] \
        or task_id in cel_tasks['reserved_tasks'] \
        or task_id in cel_tasks['scheduled_tasks']
