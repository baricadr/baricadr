import os

from baricadr.app import create_app, create_celery

from celery.signals import task_postrun

from flask_mail import Message

from .extensions import db, mail

app = create_app(config='../local.cfg')
celery = create_celery(app)


@celery.task(bind=True, name="pull_file")
def pull_file(self, path, email=None):

    self.update_state(state='PROGRESS', meta={'status': 'starting task'})

    repo = app.repos.get_repo(os.path.abspath(path))
    self.update_state(state='PROGRESS', meta={'status': 'pulling'})
    repo.pull(os.path.abspath(path))

    # TODO check md5

    self.update_state(state='PROGRESS', meta={'status': 'success'})

    if email:
        msg = Message(subject="Finished to pull",
                      body="Finished to pull %s" % path,  # TODO better text
                      sender="from@example.com",  # TODO get sender from config
                      recipients=[email])
        mail.send(msg)


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
