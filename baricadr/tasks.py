import time

from celery.signals import task_postrun
from flask import current_app

from .extensions import celery


@celery.task(bind=True)
def pull_file(self, path):
    current_app.logger.info("Starting to pull file %s" % path)
    self.update_state(state='PROGRESS', meta={'status': 'not started'})
    time.sleep(15)
    self.update_state(state='PROGRESS', meta={'status': 'transferred'})
    time.sleep(15)
    self.update_state(state='PROGRESS', meta={'status': 'md5 ok'})
    time.sleep(15)
    self.update_state(state='PROGRESS', meta={'status': 'finished ok'})

    current_app.logger.info("Finished to pull file %s" % path)
    # you can now use the db object from extensions


@task_postrun.connect
def close_session(*args, **kwargs):
    from extensions import db
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
