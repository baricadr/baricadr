from .extensions import db


class PullTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.Text(), index=True, unique=True)
    task_id = db.Column(db.String(255), index=True, unique=True)

    def __repr__(self):
        return '<PullTask {} {}>'.format(self.path, self.task_id)
