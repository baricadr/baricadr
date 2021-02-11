import time
from datetime import datetime, timedelta

from baricadr.db_models import BaricadrTask
from baricadr.extensions import db

from celery.result import AsyncResult

from . import BaricadrTestCase


class TestCelery(BaricadrTestCase):

    def setup_method(self):
        self.task_ids = []

    def teardown_method(self):
        if self.task_ids:
            for task in BaricadrTask.query.filter(BaricadrTask.task_id.in_(self.task_ids)):
                db.session.delete(task)
                db.session.commit()

    def test_zombies_cleanup(self, app):

        self.task_ids = ['id_started', 'id_pulling', 'id_freezing', 'id_waiting']
        expired_time = datetime.utcnow() - timedelta(seconds=60)

        # Create fake zombies tasks
        db.session.add(BaricadrTask(path='/repos/test_repo/subdir', type="pull", task_id='id_started', started=expired_time, status='started'))
        db.session.add(BaricadrTask(path='/repos/test_repo/subdir', type="pull", task_id='id_pulling', started=expired_time, status='pulling'))
        db.session.add(BaricadrTask(path='/repos/test_repo/subdir', type="pull", task_id='id_freezing', started=expired_time, status='freezing'))
        db.session.add(BaricadrTask(path='/repos/test_repo/subdir', type="pull", task_id='id_waiting', started=expired_time, status='waiting'))

        db.session.commit()

        time.sleep(2)

        deleted_tasks = ['id_started', 'id_pulling', 'id_freezing', 'id_waiting']

        task = app.celery.send_task('cleanup_zombie_tasks')
        AsyncResult(task.id).get(timeout=60)

        time.sleep(2)

        del_tasks = BaricadrTask.query.filter(BaricadrTask.task_id.in_(deleted_tasks))

        assert del_tasks.count() == 4

        for task in del_tasks:
            assert task.status == "failed"

    def test_cleanup(self, app):

        self.task_ids = ['id_finished', 'id_failed']
        expired_time = datetime.utcnow() - timedelta(seconds=60)

        # Create fake finished tasks
        db.session.add(BaricadrTask(path='/repos/test_repo/subdir', type="pull", task_id='id_finished', finished=expired_time, status='finished'))
        db.session.add(BaricadrTask(path='/repos/test_repo/subdir', type="pull", task_id='id_failed', finished=expired_time, status='failed'))

        db.session.commit()

        time.sleep(2)

        deleted_tasks = ['id_finished', 'id_failed']

        task = app.celery.send_task('cleanup_tasks', (30,))
        AsyncResult(task.id).get(timeout=60)

        time.sleep(2)

        del_tasks = BaricadrTask.query.filter(BaricadrTask.task_id.in_(deleted_tasks))

        assert del_tasks.count() == 0
