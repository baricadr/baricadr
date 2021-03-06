import os
import shutil
from time import sleep

from . import BaricadrTestCase


class TestApiTask(BaricadrTestCase):

    def test_get_status_unknown(self, client):
        """
        Get status from a non-existing task
        """
        response = client.get('/tasks/status/foobar')

        assert response.status_code == 404

    def test_delete_unknown(self, client):
        """
            Try to delete a non existing task
        """
        response = client.get('/tasks/remove/foobar')
        assert response.json['error'] == "Task not found in Baricadr database."
        assert response.status_code == 404

    def test_delete_task(self, client):
        """
        Try to delete an existing task
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        task_id = self.pull_quick(client, repo_dir)
        sleep(2)

        response = client.get('/tasks/remove/%s' % (task_id))

        assert response.json['info'] == "Task %s removed." % (task_id)
        assert response.status_code == 200

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def pull_quick(self, client, path, email=None):
        data = {
            'path': path
        }
        if email:
            data['email'] = email
        response = client.post('/pull', json=data)

        assert response.status_code == 200
        assert 'task' in response.json

        return response.json['task']
