import time

from baricadr.db_models import BaricadrTask
from baricadr.extensions import db

from . import BaricadrTestCase


class TestCelery(BaricadrTestCase):

    def setup_method(self):
        self.task_ids = []

    def teardown_method(self):
        if self.task_ids:
            for task in BaricadrTask.query.filter(BaricadrTask.task_id.in_(self.task_ids)):
                db.session.delete(task)
                db.session.commit()

    def test_celery_task_fails(self, app, client):

        path = '/repos/test_repo/subdir'

        task = app.celery.send_task('pull', (path, None, [None]))
        task_id = task.task_id
        self.task_ids.append(task_id)
        # Save a reference to this task in db
        pt = BaricadrTask(path=path, type="pull", task_id=task_id)
        db.session.add(pt)
        db.session.commit()

        time.sleep(10)

        res = client.get('/tasks/status/{}'.format(task_id))

        assert res.json['status'] == 'failed'
        assert res.json['error'] == "AsyncResult requires valid id, not <class 'NoneType'>"
