import os
import time
from datetime import datetime, timedelta

from baricadr.app import create_app, create_celery
from baricadr.db_models import BaricadrTask
from baricadr.extensions import db, mail

from celery.result import AsyncResult
from celery.signals import task_postrun, task_revoked

from flask_mail import Message


app = create_app(config='../local.cfg', is_worker=True)
app.app_context().push()
celery = create_celery(app)


def on_failure(self, exc, task_id, args, kwargs, einfo):

    app.logger.warning("Task %s failed. Exception raised : %s" % (task_id, str(exc)))
    dbtask = BaricadrTask.query.filter_by(task_id=task_id).one()
    dbtask.error = str(exc)

    if "email" in kwargs and kwargs['email']:
        msg = Message(subject="Failed to %s" % (dbtask.type),
                      body="Failed to %s %s. Exception raised : %s" % (dbtask.type, dbtask.path, str(exc)),  # TODO [LOW] better text
                      sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                      recipients=kwargs['email'])
        mail.send(msg)

    dbtask.status = 'failed'
    dbtask.finished = datetime.utcnow()
    db.session.commit()


def manage_repo(self, type, path, task_id, email=None, wait_for=[], sleep=0):

    # Wait a bit in case the tasks begin just before it is recorded in the db
    time.sleep(2)
    dbtask = BaricadrTask.query.filter_by(task_id=task_id).one()
    dbtask.status = 'waiting' if wait_for else 'started'
    dbtask.started = datetime.utcnow()
    db.session.commit()

    vocab = {'pull': 'pulling', 'freeze': 'freezing'}

    # For internal testing, cannot be set by api
    time.sleep(sleep)

    if wait_for:
        app.logger.debug("Waiting for tasks %s before %s '%s'" % (wait_for, vocab[type], path))
        for wait_id in wait_for:
            tries = 0
            # Wait at most MAX_TASK_DURATION, then continue
            while tries < app.config['MAX_TASK_DURATION']:
                res = AsyncResult(wait_id)
                if str(res.ready()).lower() == "true":
                    break
                time.sleep(1)
                tries += 1
        dbtask.started = datetime.utcnow()

    dbtask.status = vocab[type]
    db.session.commit()

    app.logger.debug("%s path '%s'" % (vocab[type].capitalize(), path))
    self.update_state(state='PROGRESS')

    # We don't need to resolve symlinks, if the repo is symlinks, it is checked at startup
    asked_path = os.path.abspath(path)
    repo = app.repos.get_repo(asked_path)

    if type == "pull":
        repo.pull(asked_path)
    else:
        repo.freeze(asked_path)

    dbtask.status = 'finished'

    dbtask.finished = datetime.utcnow()
    db.session.commit()

    if email:
        msg = Message(subject="Finished %s" % (vocab[type]),
                      body="Finished %s %s" % (type, path),  # TODO [LOW] better text
                      sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                      recipients=[email])
        mail.send(msg)


# Maybe fuse the tasks also?
@celery.task(bind=True, name="pull", on_failure=on_failure)
def pull(self, path, email=None, wait_for=[], sleep=0):
    manage_repo(self, 'pull', path, pull.request.id, email=email, wait_for=wait_for, sleep=sleep)


@celery.task(bind=True, name="freeze", on_failure=on_failure)
def freeze(self, path, email=None, wait_for=[], sleep=0):
    manage_repo(self, 'freeze', path, freeze.request.id, email=email, wait_for=wait_for, sleep=sleep)


@celery.task(bind=True, name="cleanup_zombie_tasks")
def cleanup_zombie_tasks(self, max_task_duration):
    """
    Look at the list of tasks in the database and check if they are running or in queue.
    If for some reason a task is in the db but not running/in queue, it means that it is finished or that it got interrupted.
    """

    max_date = datetime.utcnow() - timedelta(seconds=max_task_duration)

    self.update_state(state='PROGRESS')

    num = 0
    # Filter tasks older than max_delay and kill them
    running_tasks = BaricadrTask.query.filter(BaricadrTask.started < max_date)
    for rt in running_tasks:
        # Do not check tasks in 'waiting' state
        if rt.status in ['started', 'pulling', 'freezing']:
            app.logger.debug("Checking zombie for task '%s' %s on path '%s'" % (rt.task_id, rt.type, rt.path))
            AsyncResult(rt.task_id).revoke(terminate=True)
            # Actually set status here and not in signal so we can test it...
            rt.status = 'failed'
            rt.finished = datetime.utcnow()
            num += 1
        db.session.commit()
    app.logger.debug("%s zombie tasks killed (%s remaining)" % (num, running_tasks.count() - num))


@celery.task(bind=True, name="cleanup_tasks")
def cleanup_tasks(self, cleanup_age):
    """
        Cleanup finished and failed tasks
    """

    max_date = datetime.utcnow() - timedelta(seconds=cleanup_age)
    finished_tasks = BaricadrTask.query.filter(BaricadrTask.status.in_(["failed", "finished"]), BaricadrTask.finished < max_date)

    num = 0
    for ft in finished_tasks:
        app.logger.debug("Clearing finished task %s with status %s (type = %s, path = %s)'" % (ft.task_id, ft.status, ft.type, ft.path))
        db.session.delete(ft)
        db.session.commit()
        num += 1

    app.logger.debug("Cleared %s finished tasks" % (num))
    self.update_state(state='PROGRESS')


# Trigger when a task is revoked
@task_revoked.connect
def on_task_revoked(**kwargs):
    # Signal is sent twice, so only catch it once
    if str(kwargs['signum']) == 'Signals.SIGTERM':

        request = kwargs['request']
        path = request.args[0]
        email = request.args[1]

        if email:
            msg = Message(subject="Failed to %s" % (request.task),
                          body="Failed to %s %s, task was removed after expiring" % (request.task, path),  # TODO [LOW] better text
                          sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                          recipients=email)
            mail.send(msg)


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
