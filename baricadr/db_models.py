from datetime import datetime

from .extensions import db


# Storing information in an sql db as getting it from finished celery tasks is not possible/reliable

class BaricadrTask(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    path = db.Column(db.Text(), index=True, nullable=False)
    type = db.Column(db.String(255), index=True, nullable=False)
    task_id = db.Column(db.String(255), index=True, unique=True, nullable=False)
    status = db.Column(db.String(255), nullable=False, default='new')
    created = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    started = db.Column(db.DateTime())
    finished = db.Column(db.DateTime())
    error = db.Column(db.Text())

    def __repr__(self):
        return '<BaricadrTask {} {} {} {}>'.format(self.type, self.path, self.task_id, self.status)

    def logfile_path(self, app, task_id):
        return "{}/{}_{}.log".format(app.config['TASK_LOG_DIR'], self.created.strftime("%Y-%m-%d_%H-%M-%S"), task_id)
