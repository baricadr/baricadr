import time

from baricadr import create_app, create_celery
from celery.signals import task_postrun
from flask_mail import Message

from .extensions import db, mail

app = create_app(config='../local.cfg')
celery = create_celery(app)


@celery.task(bind=True, name="pull_file")
def pull_file(self, path):
    msg = Message(subject="Beginning to pull",
                  body="Beginning to pull %s" % path,
                  sender="from@example.com",
                  recipients=["abretaud@irisa.fr"])
    mail.send(msg)
    self.update_state(state='PROGRESS', meta={'status': 'not started'})
    time.sleep(15)
    self.update_state(state='PROGRESS', meta={'status': 'transferred'})
    time.sleep(15)
    self.update_state(state='PROGRESS', meta={'status': 'md5 ok'})
    time.sleep(15)
    self.update_state(state='PROGRESS', meta={'status': 'finished ok'})
    msg = Message(subject="Finished to pull",
                  body="Finished to pull %s" % path,
                  sender="from@example.com",
                  recipients=["abretaud@irisa.fr"])
    mail.send(msg)


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
