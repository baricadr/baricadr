import os
import time
from datetime import datetime, timedelta

from baricadr.app import create_app, create_celery
from baricadr.db_models import BaricadrTask
from baricadr.extensions import db, mail
from baricadr.utils import celery_task_is_in_queue, get_celery_tasks

from celery.signals import task_postrun, task_revoked

from flask_mail import Message


app = create_app(config='../local.cfg', is_worker=True)
app.app_context().push()
celery = create_celery(app)


def on_failure(self, exc, task_id, args, kwargs, einfo):

    app.logger.warning("Task %s failed. Exception raised: %s" % (task_id, str(exc)))
    dbtask = BaricadrTask.query.filter_by(task_id=task_id).one()
    dbtask.error = str(exc)

    # args[1] is the email adsress
    if len(args) > 2 and args[1] and len(args[1]) > 0:
        body = """Hello,
One of your BARICADR {task} task on path '{path}' failed, with the following error:
{error}
Contact the administrator for more info.
Cheers
"""
        msg = Message(subject="BARICADR: {task} task on {path} failed".format(task=dbtask.type, path=dbtask.path),
                      body=body.format(task=dbtask.type, path=dbtask.path, error=str(exc)),
                      sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                      recipients=[args[1]])
        mail.send(msg)

    dbtask.status = 'failed'
    dbtask.finished = datetime.utcnow()
    db.session.commit()


def run_repo_action(self, type, path, task_id, email=None, wait_for=[], sleep=0):

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
            while celery_task_is_in_queue(app.celery, wait_id):
                time.sleep(10)
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
        body = """Hello,
As you asked, BARICADR has finished {verb} the following path: {path}.
Cheers
"""
        msg = Message(subject="BARICADR: finished {verb} {path}".format(verb=vocab[type], path=path),
                      body=body.format(verb=vocab[type], path=path),
                      sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                      recipients=[email])
        mail.send(msg)


# Maybe fuse the tasks also?
@celery.task(bind=True, name="pull", on_failure=on_failure)
def pull(self, path, email=None, wait_for=[], sleep=0):
    run_repo_action(self, 'pull', path, pull.request.id, email=email, wait_for=wait_for, sleep=sleep)


@celery.task(bind=True, name="freeze", on_failure=on_failure)
def freeze(self, path, email=None, wait_for=[], sleep=0):
    run_repo_action(self, 'freeze', path, freeze.request.id, email=email, wait_for=wait_for, sleep=sleep)


@celery.task(bind=True, name="cleanup_zombie_tasks")
def cleanup_zombie_tasks(self):
    """
    Look at the list of tasks in the database and check if they are running or in queue.
    If for some reason a task is in the db but not running/in queue, it means that it is finished or that it got interrupted.
    """

    cel_tasks = get_celery_tasks(app.celery)

    self.update_state(state='PROGRESS')

    num = 0
    # Filter tasks not yet finished/failed
    running_tasks = BaricadrTask.query.filter(BaricadrTask.status.notin_(["failed", "finished"]))
    for rt in running_tasks:
        if rt.task_id not in cel_tasks['active_tasks'] \
           and rt.task_id not in cel_tasks['reserved_tasks'] \
           and rt.task_id not in cel_tasks['scheduled_tasks']:

            app.logger.debug("Found zombie state for task '%s' %s on path '%s'" % (rt.task_id, rt.type, rt.path))
            rt.status = 'failed'
            rt.finished = datetime.utcnow()
            num += 1
        db.session.commit()
    app.logger.debug("%s zombie tasks killed (%s remaining)" % (num, running_tasks.count() - num))


@celery.task(bind=True, name="cleanup_tasks")
def cleanup_tasks(self, cleanup_age):
    """
        Cleanup old finished and failed tasks from db
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
            body = """Hello,
One of your BARICADR task '{task}' on path '{path}' was terminated prematurely.
Contact the administrator for more info.
Cheers
"""
            msg = Message(subject="BARICADR: task {task} on {path} failed".format(task=request.task, path=path),
                          body=body.format(task=request.task, path=path),
                          sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                          recipients=[email])
            mail.send(msg)


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
