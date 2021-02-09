def get_celery_worker_status(app):
    i = app.control.inspect()
    availability = i.ping()
    # stats = i.stats()
    result = {
        'availability': availability,
        # 'stats': stats,
    }
    return result
