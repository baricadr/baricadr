import os
import shutil
from time import sleep

from . import BaricadrTestCase


class TestApi(BaricadrTestCase):

    def test_pull_missing_path(self, client):
        data = {
            'files': '/foo/bar'
        }
        response = client.post('/pull', json=data)

        assert response.status_code == 400
        assert response.json == {'error': 'Missing "path"'}

    def test_pull_wrong_email(self, client):
        data = {
            'path': '/foo/bar',
            'email': 'x'
        }
        response = client.post('/pull', json=data)

        assert response.status_code == 400
        assert response.json == {"error": "The email address is not valid. It must have exactly one @-sign."}

    def test_get_status_unknown(self, client):
        response = client.get('/status/foobar')

        # TODO maybe we should send a 404 error, but celery can't say if the task is finished or doesn't exist
        assert response.json == {'finished': 'false', 'error': 'false', 'info': None}
        assert response.status_code == 200

    def test_pull_success(self, app, client):

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        data = {
            'path': repo_dir
        }
        response = client.post('/pull', json=data)

        assert response.status_code == 200
        assert 'task' in response.json

        pull_id = response.json['task']

        # Wait for the task to run
        wait = 0
        while wait < 10:
            sleep(2)

            response = client.get('/status/%s' % pull_id)

            assert response.status_code == 200

            if response.json['finished'] == "true":
                break
            else:
                assert response.json['error'] == 'false'
            wait += 1

        assert response.json == {'finished': 'true', 'error': 'false', 'info': None}

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
