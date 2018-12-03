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
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_race(self, app, client):
        """
        Try to pull a dir twice at the same time
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        pull_id = self.pull_quick(client, repo_dir)
        pull_id_2 = self.pull_quick(client, repo_dir)

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
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_race_subdir(self, app, client):
        """
        Try to pull a dir and subdir at the same time
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        pull_id = self.pull_quick(client, repo_dir)
        pull_id_2 = self.pull_quick(client, repo_dir + '/subsubdir')

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
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_race_updir(self, app, client):
        """
        Try to pull a dir and subdir at the same time
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        pull_id = self.pull_quick(client, repo_dir + '/subsubdir')
        pull_id_2 = self.pull_quick(client, repo_dir)

        assert pull_id != pull_id_2

        # Wait for the tasks to run
        self.wait_for_pull(client, pull_id)
        self.wait_for_pull(client, pull_id_2)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

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
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

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
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')
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
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

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
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'subfile content\n'

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_local_old(self, app, client):
        """
        Try to pull a dir containing some locally deleted data
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'subfile content\n'

        # Modify in local repo and change its modification time
        with open(repo_dir + '/subfile.txt', 'w') as local_file:
            local_file.write('This was touched locally\n')

        new_time = os.stat(repo_dir + '/subfile.txt').st_mtime - 100000000
        os.utime(repo_dir + '/subfile.txt', (new_time, new_time))

        # Try to pull a dir already pulled just before
        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'This was touched locally\n'

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_exclude(self, app, client):
        """
        Try to pull a dir with an exclude rule
        """

        repo_dir = '/repos/test_repo_exclude/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert not os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.tsv')

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_exclude_multiple(self, app, client):
        """
        Try to pull a dir with an exclude rule
        """

        repo_dir = '/repos/test_repo_exclude_multiple/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert not os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')
        assert not os.path.exists(repo_dir + '/subsubdir/poutrelle.tsv')

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

    def wait_for_pull(self, client, pull_id):
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

    def pull_and_wait(self, client, path):

        pull_id = self.pull_quick(client, path)
        self.wait_for_pull(client, pull_id)

# TODO better test for pulling a dir when a subdir is already pulling: multiple subdirs in parallel, timeout waiting
# TODO test checksum
# TODO implement freezing tasks (manual and automatic)
# TODO store in db the freezed file => consult it with baricadr ls
# TODO document how to run backups: disable --delete mode!! + how to handle moved data (not a problem with archive)?
