import os
import time

import baricadr.api
from baricadr.app import create_app, create_celery
from baricadr.db_models import PullTask

from celery.result import AsyncResult
from celery.signals import task_postrun

from flask_mail import Message

from .extensions import db, mail


app = create_app(config='../local.cfg')
celery = create_celery(app)


@celery.task(bind=True, name="pull_file")
def pull_file(self, path, email=None, wait_for=[]):

    wait_for_failed = False
    if wait_for:
        app.logger.debug("Waiting for tasks %s before pulling '%s'" % (wait_for, path))
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
                app.logger.warning("Waited to long for task '%s', giving up" % (wait_id))
                break

    if not wait_for_failed:
        app.logger.debug("Pulling path '%s'" % (path))

        self.update_state(state='PROGRESS', meta={'status': 'starting task'})

        # We don't need to resolve symlinks, if the repo is symlinks, it is checked at startup
        asked_path = os.path.abspath(path)

        repo = app.repos.get_repo(asked_path)
        self.update_state(state='PROGRESS', meta={'status': 'pulling'})
        repo.pull(asked_path)

        # TODO check md5

        self.update_state(state='PROGRESS', meta={'status': 'success'})
    else:
        self.update_state(state='PROGRESS', meta={'status': 'failed'})

    app.logger.debug("Deleting task '%s' from db" % pull_file.request.id)
    PullTask.query.filter_by(task_id=pull_file.request.id).delete()
    db.session.commit()

    if email:
        if wait_for_failed:
            msg = Message(subject="Failed to pull",
                          body="Failed to pull %s" % path,  # TODO better text
                          sender="from@example.com",  # TODO get sender from config
                          recipients=[email])
        else:
            msg = Message(subject="Finished to pull",
                          body="Finished to pull %s" % path,  # TODO better text
                          sender="from@example.com",  # TODO get sender from config
                          recipients=[email])
        mail.send(msg)


@celery.task(bind=True, name="cleanup_zombie_tasks")
def cleanup_zombie_tasks(self):
    """
    Look at the list of tasks in the database and check if they are running or in queue.
    If for some reason a task is in the db but not running/in queue, it means that it got interrupted.
    """

    self.update_state(state='PROGRESS', meta={'status': 'starting task'})

    num = 0
    running_tasks = PullTask.query.all()
    for rt in running_tasks:
        app.logger.debug("Checking zombie for task '%s' on path '%s'" % (rt.task_id, rt.path))
        failed_status = False
        try:
            status = baricadr.api.status_pull(rt.task_id).json
        except:  # noqa: E722
            failed_status = True

        if failed_status or (status['finished'] == "true"):
            app.logger.warning("Detected zombie task '%s' for path '%s'" % (rt.task_id, rt.path))
            # TODO auto reschedule zombies instead of just removing them?
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
