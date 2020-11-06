from datetime import datetime
import os
import time

import baricadr.api
from baricadr.app import create_app, create_celery
from baricadr.db_models import BaricadrTask

from celery.result import AsyncResult
from celery.signals import task_postrun

from flask_mail import Message

from .extensions import db, mail


app = create_app(config='../local.cfg', is_worker=True)
celery = create_celery(app)


# TODO [HI] test this
def on_failure(self, exc, task_id, args, kwargs, einfo):

    dbtask = BaricadrTask.query.filter_by(task_id=task_id).one()
    dbtask.status = 'failed'
    dbtask.finished = datetime.utcnow()
    db.session.commit()


@celery.task(bind=True, name="pull", on_failure=on_failure)
def pull(self, path, email=None, wait_for=[]):

    # Wait a bit in case the tasks begin just before it is recorded in the db
    time.sleep(2)
    dbtask = BaricadrTask.query.filter_by(task_id=pull.request.id).one()
    dbtask.status = 'started' if wait_for else 'waiting'
    dbtask.started = datetime.utcnow()
    db.session.commit()

    wait_for_failed = False
    if wait_for:
        app.logger.debug("Waiting for tasks %s before pulling '%s'" % (wait_for, path))
        for wait_id in wait_for:
            tries = 0
            while tries < 21600:  # Wait at most 6h  #TODO [HI] make the max wait delay configurable
                res = AsyncResult(wait_id)
                if str(res.ready()).lower() == "true":
                    break
                time.sleep(2)
                tries += 1
            if tries == 21600:
                wait_for_failed = True
                app.logger.warning("Waited too long for task '%s', giving up" % (wait_id))
                break

    if not wait_for_failed:
        app.logger.debug("Pulling path '%s'" % (path))

        self.update_state(state='PROGRESS', meta={'status': 'starting task'})

        # We don't need to resolve symlinks, if the repo is symlinks, it is checked at startup
        asked_path = os.path.abspath(path)

        repo = app.repos.get_repo(asked_path)
        self.update_state(state='PROGRESS', meta={'status': 'pulling'})

        dbtask.status = 'pulling'
        db.session.commit()

        repo.pull(asked_path)

        self.update_state(state='PROGRESS', meta={'status': 'success'})
        dbtask.status = 'finished'
    else:
        self.update_state(state='PROGRESS', meta={'status': 'failed'})
        dbtask.status = 'failed'

    # TODO [HI] how do we set in finished/failed state if there is an exception?
    dbtask.finished = datetime.utcnow()
    db.session.commit()

    if email:
        if wait_for_failed:
            msg = Message(subject="Failed to pull",
                          body="Failed to pull %s" % path,  # TODO [LOW] better text
                          sender="from@example.com",  # TODO [LOW] get sender from config
                          recipients=[email])
        else:
            msg = Message(subject="Finished to pull",
                          body="Finished to pull %s" % path,  # TODO [LOW] better text
                          sender="from@example.com",  # TODO [LOW] get sender from config
                          recipients=[email])
        mail.send(msg)


@celery.task(bind=True, name="freeze", on_failure=on_failure)
def freeze(self, path, email=None, wait_for=[]):

    # Wait a bit in case the tasks begin just before it is recorded in the db
    time.sleep(2)
    dbtask = BaricadrTask.query.filter_by(task_id=freeze.request.id).one()
    dbtask.status = 'started' if wait_for else 'waiting'
    dbtask.started = datetime.utcnow()
    db.session.commit()
    # TODO [HI] update this code to sync with pull above (+refactor?)

    wait_for_failed = False
    if wait_for:
        app.logger.debug("Waiting for tasks %s before freezing '%s'" % (wait_for, path))
        for wait_id in wait_for:
            tries = 0
            while tries < 21600:  # Wait at most 6h
                res = AsyncResult(wait_id)
                if str(res.ready()).lower() == "true":
                    break
                time.sleep(2)
                tries += 1
            if tries == 21600:
                wait_for_failed = True
                app.logger.warning("Waited too long for task '%s', giving up" % (wait_id))
                break

    if not wait_for_failed:
        app.logger.debug("Freezing path '%s'" % (path))

        self.update_state(state='PROGRESS', meta={'status': 'starting task'})

        # We don't need to resolve symlinks, if the repo is symlinks, it is checked at startup
        asked_path = os.path.abspath(path)

        repo = app.repos.get_repo(asked_path)
        self.update_state(state='PROGRESS', meta={'status': 'freezing'})

        dbtask.status = 'freezing'
        db.session.commit()

        repo.freeze(asked_path)

        self.update_state(state='PROGRESS', meta={'status': 'success'})
        dbtask.status = 'finished'
    else:
        self.update_state(state='PROGRESS', meta={'status': 'failed'})
        dbtask.status = 'failed'

    # TODO [HI] how do we set in finished/failed state if there is an exception?
    dbtask.finished = datetime.utcnow()
    db.session.commit()

    if email:
        if wait_for_failed:
            msg = Message(subject="Failed to freeze",
                          body="Failed to freeze %s" % path,  # TODO [LOW] better text
                          sender="from@example.com",  # TODO [LOW] get sender from config
                          recipients=[email])
        else:
            msg = Message(subject="Finished to freeze",
                          body="Finished to freeze %s" % path,  # TODO [LOW] better text
                          sender="from@example.com",  # TODO [LOW] get sender from config
                          recipients=[email])
        mail.send(msg)


@celery.task(bind=True, name="cleanup_zombie_tasks")
def cleanup_zombie_tasks(self):
    """
    Look at the list of tasks in the database and check if they are running or in queue.
    If for some reason a task is in the db but not running/in queue, it means that it is finished or that it got interrupted.
    """

    # TODO [HI] delete old tasks in zombie task to keep track of finished tasks for a while (configurable delay)

    self.update_state(state='PROGRESS', meta={'status': 'starting task'})

    num = 0
    running_tasks = BaricadrTask.query.all()
    for rt in running_tasks:
        app.logger.debug("Checking zombie for task '%s' %s on path '%s'" % (rt.task_id, rt.type, rt.path))
        failed_status = False
        try:
            status = baricadr.api.task_show(rt.task_id).json
        except:  # noqa: E722
            failed_status = True

        if failed_status or (status['finished'] == "true"):
            app.logger.warning("Detected zombie task '%s' for path '%s'" % (rt.task_id, rt.path))
            # We're not auto rescheduling zombies as we don't know what happened => it could be dangerous (infinite loop, data overwriting, ...)
            db.session.delete(rt)
            db.session.commit()
            num += 1

    app.logger.debug("%s zombie tasks killed (%s remaining)" % (num, len(running_tasks) - num))

    self.update_state(state='PROGRESS', meta={'status': '%s zombie tasks killed (%s remaining)' % (num, len(running_tasks) - num)})


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
