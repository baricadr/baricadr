import os
import shutil
from time import sleep

from . import BaricadrTestCase


class TestApi(BaricadrTestCase):

    def test_pull_missing_path(self, client):
        """
        Pull without a proper path
        """
        data = {
            'files': '/foo/bar'
        }
        response = client.post('/pull', json=data)

        assert response.status_code == 400
        assert response.json == {'error': 'Missing "path"'}

    def test_pull_wrong_email(self, client):
        """
        Pull with wrong email address
        """
        data = {
            'path': '/foo/bar',
            'email': 'x'
        }
        response = client.post('/pull', json=data)

        assert response.status_code == 400
        assert response.json == {"error": "The email address is not valid. It must have exactly one @-sign."}

    def test_get_status_unknown(self, client):
        """
        Get status from a non-existing task
        """
        response = client.get('/status/foobar')

        # TODO maybe we should send a 404 error, but celery can't say if the task is finished or doesn't exist
        assert response.json == {'finished': 'false', 'error': 'false', 'info': None}
        assert response.status_code == 200

    def test_pull_success(self, app, client):
        """
        Try to pull a dir in normal conditions
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_race(self, app, client):
        """
        Try to pull a dir twice at the same time
        """

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

        # Ask immediately, the first one should not be finished yet
        response = client.post('/pull', json=data)

        assert response.status_code == 200
        assert 'task' in response.json

        pull_id_2 = response.json['task']

        assert pull_id == pull_id_2

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

    def test_pull_twice(self, app, client):
        """
        Try to pull a subdir already pulled just before
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        # Try to pull a file already pulled just before
        self.pull_and_wait(client, repo_dir + '/subsubdir')

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_local_add(self, app, client):
        """
        Try to pull a dir containing other local-only data
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        # Copy a local-only file in local repo
        shutil.copyfile(repo_dir + '/subfile.txt', repo_dir + '/local_new_file.txt')

        # Try to pull a file already pulled just before
        self.pull_and_wait(client, repo_dir + '/subsubdir')

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert os.path.exists(repo_dir + '/local_new_file.txt')

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_local_mod(self, app, client):
        """
        Try to pull a dir containing some locally modified data
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'subfile content\n'

        # Modify in local repo
        with open(repo_dir + '/subfile.txt', 'w') as local_file:
            local_file.write('This was touched locally\n')

        # Try to pull a file already pulled just before
        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'This was touched locally\n'

        # Modify in local repo with a very short string
        with open(repo_dir + '/subfile.txt', 'w') as local_file:
            local_file.write('This\n')

        # Try to pull a file already pulled just before
        self.pull_and_wait(client, repo_dir)

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'This\n'

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_local_del(self, app, client):
        """
        Try to pull a dir containing some locally deleted data
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'subfile content\n'

        # delete a file from local repo
        os.unlink(repo_dir + '/subfile.txt')

        # Try to pull a dir already pulled just before
        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'subfile content\n'

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def pull_and_wait(self, client, path):
        data = {
            'path': path
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

# TODO test local modification but older file
# TODO test pulling /
# TODO test checksum
# TODO test emails
# TODO test excludes
# TODO implement freezing tasks
