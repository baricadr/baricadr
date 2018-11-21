import os

import baricadr.api
from baricadr.app import create_app, create_celery
from baricadr.db_models import PullTask

from celery.signals import task_postrun

from flask_mail import Message

from .extensions import db, mail

app = create_app(config='../local.cfg')
celery = create_celery(app)


@celery.task(bind=True, name="pull_file")
def pull_file(self, path, email=None):

    self.update_state(state='PROGRESS', meta={'status': 'starting task'})

    asked_path = os.path.abspath(path)  # FIXME use realpath to resolve symlinks?

    repo = app.repos.get_repo(asked_path)
    self.update_state(state='PROGRESS', meta={'status': 'pulling'})
    repo.pull(asked_path)

    # TODO check md5

    self.update_state(state='PROGRESS', meta={'status': 'success'})

    if email:
        msg = Message(subject="Finished to pull",
                      body="Finished to pull %s" % path,  # TODO better text
                      sender="from@example.com",  # TODO get sender from config
                      recipients=[email])
        mail.send(msg)


# TODO call this on startup and regularly
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
        status = baricadr.api.status_pull(rt.task_id)
        if status['finished'] == "true":
            app.logger.warning("Detected zombie task '%s' for path '%s'" % (rt.task_id, rt.path))
            # TODO auto reschedule zombies instead of just removing them?
            app.db.session.delete(rt)
            app.db.session.commit()
            num += 1

    self.update_state(state='PROGRESS', meta={'status': '%s zombie tasks killed (%s remaining)' % (num, len(running_tasks) - num)})


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
