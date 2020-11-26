import os
import time
from datetime import datetime, timedelta

from baricadr.app import create_app, create_celery
from baricadr.db_models import BaricadrTask
from baricadr.extensions import db, mail

from celery.result import AsyncResult
from celery.signals import task_postrun

from flask_mail import Message


app = create_app(config='../local.cfg', is_worker=True)
app.app_context().push()
celery = create_celery(app)


def on_failure(self, exc, task_id, args, kwargs, einfo):
    dbtask = BaricadrTask.query.filter_by(task_id=task_id).one()

    if "email" in kwargs and kwargs['email']:
        msg = Message(subject="Failed to %s" % (dbtask.type),
                      body="Failed to %s %s" % (dbtask.type, dbtask.path),  # TODO [LOW] better text
                      sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                      recipients=kwargs['email'])
        mail.send(msg)

    dbtask.status = 'failed'
    dbtask.finished = datetime.utcnow()
    db.session.commit()


def manage_repo(self, type, path, task_id, email=None, wait_for=[]):

    # Wait a bit in case the tasks begin just before it is recorded in the db
    time.sleep(2)
    dbtask = BaricadrTask.query.filter_by(task_id=task_id).one()
    dbtask.status = 'started' if wait_for else 'waiting'
    dbtask.started = datetime.utcnow()
    db.session.commit()

    vocab = {'pull': 'pulling', 'freeze': 'freezing'}

    wait_for_failed = False
    if wait_for:
        app.logger.debug("Waiting for tasks %s before %s '%s'" % (wait_for, vocab[type], path))
        for wait_id in wait_for:
            tries = 0
            while tries < app.config['MAX_TASK_DURATION']:  # Wait at most 6h
                res = AsyncResult(wait_id)
                if str(res.ready()).lower() == "true":
                    break
                time.sleep(1)
                tries += 1
            if tries == app.config['MAX_TASK_DURATION']:
                wait_for_failed = True
                app.logger.warning("Waited too long for task '%s', giving up" % (wait_id))
                break

    if not wait_for_failed:
        app.logger.debug("%s path '%s'" % (vocab[type].capitalize(), path))

        self.update_state(state='PROGRESS', meta={'status': 'starting task'})

        # We don't need to resolve symlinks, if the repo is symlinks, it is checked at startup
        asked_path = os.path.abspath(path)

        repo = app.repos.get_repo(asked_path)
        self.update_state(state='PROGRESS', meta={'status': vocab[type]})

        dbtask.status = vocab[type]
        db.session.commit()

        if type == "pull":
            repo.pull(asked_path)
        else:
            repo.freeze(asked_path)

        self.update_state(state='PROGRESS', meta={'status': 'success'})
        dbtask.status = 'finished'

    else:
        self.update_state(state='PROGRESS', meta={'status': 'failed'})
        dbtask.status = 'failed'

    dbtask.finished = datetime.utcnow()
    db.session.commit()

    if email:
        if wait_for_failed:
            msg = Message(subject="Failed to %s" % (type),
                          body="Failed to %s %s" % (type, path),  # TODO [LOW] better text
                          sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                          recipients=[email])
        else:
            msg = Message(subject="Finished %s" % (vocab[type]),
                          body="Finished %s %s" % (type, path),  # TODO [LOW] better text
                          sender=app.config.get('SENDER_EMAIL', 'from@example.com'),
                          recipients=[email])
        mail.send(msg)


# Maybe fuse the tasks also?
@celery.task(bind=True, name="pull", on_failure=on_failure)
def pull(self, path, email=None, wait_for=[]):
    manage_repo(self, 'pull', path, pull.request.id, email=email, wait_for=wait_for)


@celery.task(bind=True, name="freeze", on_failure=on_failure)
def freeze(self, path, email=None, wait_for=[]):
    manage_repo(self, 'freeze', path, freeze.request.id, email=email, wait_for=wait_for)


@celery.task(bind=True, name="cleanup_zombie_tasks")
def cleanup_zombie_tasks(self):
    """
    Look at the list of tasks in the database and check if they are running or in queue.
    If for some reason a task is in the db but not running/in queue, it means that it is finished or that it got interrupted.
    """

    max_delay = app.config['MAX_TASK_DURATION']
    max_date = datetime.utcnow() - timedelta(seconds=max_delay)

    self.update_state(state='PROGRESS', meta={'status': 'starting task'})

    num = 0
    # Filter tasks older than max_delay and kill them
    running_tasks = BaricadrTask.query.filter(BaricadrTask.started < max_date)
    for rt in running_tasks:
        # Kill celery task process if it's still running (or state unknown)
        # Task status should be reliable enough..?
        # No checking task with "waiting" status, they should fail on their own
        if rt.status == 'started':
            app.logger.debug("Checking zombie for task '%s' %s on path '%s'" % (rt.task_id, rt.type, rt.path))
            AsyncResult(rt.task_id).revoke(terminate=True)
            num += 1
        # Should we delete the task from db also?
    app.logger.debug("%s zombie tasks killed (%s remaining)" % (num, running_tasks.count() - num))


@celery.task(bind=True, name="cleanup_tasks")
def cleanup_tasks(self):
    """
        Cleanup finished and failed tasks
    """

    finished_tasks = BaricadrTask.query.filter(BaricadrTask.status.in_(["failed", "finished"]))

    num = 0
    for ft in finished_tasks:
        app.logger.debug("Clearing finished task %s with status %s (type = %s, path = %s)'" % (ft.task_id, ft.status, ft.type, ft.path))
        db.session.delete(ft)
        db.session.commit()
        num += 1

    app.logger.debug("Cleared %s finished tasks" % (num))
    self.update_state(state='PROGRESS', meta={'status': "Cleared %s finished tasks" % (num)})


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
