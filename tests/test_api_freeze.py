import os
import shutil
from time import sleep

from . import BaricadrTestCase


class TestApiFreeze(BaricadrTestCase):

    template_repo = "/baricadr/test-data/test-repo/"
    testing_repo = "/repos/test_repo_freeze/"
    testing_repos = [
        "/repos/test_repo_freeze/",
        "/repos/test_repo_freeze_exclude/",
        "/repos/test_repo_freeze_exclude_multiple/"
    ]

    def setup_method(self):
        for repo in self.testing_repos:
            if os.path.exists(repo):
                shutil.rmtree(repo)
            shutil.copytree(self.template_repo, repo)

    def teardown_method(self):
        for repo in self.testing_repos:
            if os.path.exists(repo):
                shutil.rmtree(repo)

    def test_freeze_missing_path(self, client):
        """
        Freeze without a proper path
        """
        data = {
            'files': '/foo/bar'
        }
        response = client.post('/freeze', json=data)

        assert response.status_code == 400
        assert response.json == {'error': 'Missing "path"'}

    def test_freeze_wrong_email(self, client):
        """
        Freeze with wrong email address
        """
        data = {
            'path': '/foo/bar',
            'email': 'x'
        }
        response = client.post('/freeze', json=data)

        assert response.status_code == 400
        assert response.json == {"error": "The email address is not valid. It must have exactly one @-sign."}

    def test_freeze_single(self, app, client):
        """
        Try to freeze a single file in normal conditions
        """

        to_freeze = os.path.join(self.testing_repo, 'subdir', 'subfile.txt')

        self.set_old_atime(to_freeze, age=3600 * 5000, recursive=False)

        self.freeze_and_wait(client, to_freeze)

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_subdir(self, app, client):
        """
        Try to freeze a dir in normal conditions
        """

        repo_dir = os.path.join(self.testing_repo, 'subdir')

        self.set_old_atime(repo_dir, age=3600 * 5000)

        self.freeze_and_wait(client, repo_dir)

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_rootdir(self, app, client):
        """
        Try to freeze a dir in normal conditions
        """

        repo_dir = os.path.join(self.testing_repo)

        self.set_old_atime(repo_dir, age=3600 * 5000)

        self.freeze_and_wait(client, repo_dir)

        not_expected_freezed = [
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

        os.path.exists(repo_dir)

    def test_freeze_race(self, app, client):
        """
        Try to freeze a dir twice at the same time
        """

        repo_dir = os.path.join(self.testing_repo, 'subdir')

        self.set_old_atime(repo_dir, age=3600 * 5000)

        freeze_id = self.freeze_quick(client, repo_dir)
        freeze_id_2 = self.freeze_quick(client, repo_dir)

        assert freeze_id == freeze_id_2

        # Wait for the task to run
        wait = 0
        while wait < 10:
            sleep(2)

            response = client.get('/status/%s' % freeze_id)

            assert response.status_code == 200

            if response.json['task']['finished'] == "true":
                break
            else:
                assert response.json['task']['error'] == 'false'
            wait += 1

        assert response.json['task'] == {'finished': 'true', 'error': 'false', 'info': None}

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_race_subdir(self, app, client):
        """
        Try to freeze a dir and subdir at the same time
        """

        repo_dir = os.path.join(self.testing_repo, 'subdir')

        self.set_old_atime(repo_dir, age=3600 * 5000)

        freeze_id = self.freeze_quick(client, repo_dir)
        freeze_id_2 = self.freeze_quick(client, repo_dir + '/subsubdir')

        assert freeze_id == freeze_id_2

        # Wait for the task to run
        wait = 0
        while wait < 10:
            sleep(2)

            response = client.get('/status/%s' % freeze_id)

            assert response.status_code == 200

            if response.json['task']['finished'] == "true":
                break
            else:
                assert response.json['task']['error'] == 'false'
            wait += 1

        assert response.json['task'] == {'finished': 'true', 'error': 'false', 'info': None}

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_race_updir(self, app, client):
        """
        Try to freeze a dir and subdir at the same time
        """

        repo_dir = os.path.join(self.testing_repo, 'subdir')

        self.set_old_atime(repo_dir, age=3600 * 5000)

        freeze_id = self.freeze_quick(client, repo_dir + '/subsubdir')
        freeze_id_2 = self.freeze_quick(client, repo_dir)

        assert freeze_id != freeze_id_2

        # Wait for the tasks to run
        self.wait_for_freeze(client, freeze_id)
        self.wait_for_freeze(client, freeze_id_2)

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_twice(self, app, client):
        """
        Try to freeze a subdir already freezed just before
        """

        repo_dir = os.path.join(self.testing_repo, 'subdir')

        self.set_old_atime(repo_dir, age=3600 * 5000)

        self.freeze_and_wait(client, repo_dir)

        # Try to freeze a file already freezed just before
        self.freeze_and_wait(client, repo_dir + '/subsubdir')

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_local_add(self, app, client):
        """
        Try to freeze a dir containing other local-only data
        """

        repo_dir = os.path.join(self.testing_repo, 'subdir')

        # Copy a local-only file in local repo
        shutil.copyfile(os.path.join(self.testing_repo, 'subdir', 'subfile.txt'), os.path.join(self.testing_repo, 'subdir', 'local_new_file.txt'))
        # Set atime AFTER copy, else it will be reset
        self.set_old_atime(repo_dir, age=3600 * 5000)

        self.freeze_and_wait(client, repo_dir)

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir', 'local_new_file.txt')
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_local_mod(self, app, client):
        """
        Try to freeze a dir containing some locally modified data
        """

        repo_dir = os.path.join(self.testing_repo, 'subdir')

        self.set_old_atime(repo_dir, age=3600 * 5000)

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'subfile content\n'

        # Modify in local repo
        with open(repo_dir + '/subfile.txt', 'w') as local_file:
            local_file.write('This was touched locally\n')

        self.freeze_and_wait(client, repo_dir)

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
        ]

        expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'This was touched locally\n'

        # Modify in local repo with a very short string
        with open(repo_dir + '/subfile.txt', 'w') as local_file:
            local_file.write('This\n')

        # Try to freeze a file already freezed just before
        self.freeze_and_wait(client, repo_dir)

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'This\n'

    def test_freeze_api_exclude(self, app, client):
        """
        Try to freeze a dir with an exclude rule
        """

        repo_dir = os.path.join('/repos/test_repo_freeze_exclude')

        self.set_old_atime(repo_dir, age=3600 * 5000)

        self.freeze_and_wait(client, repo_dir)

        not_expected_freezed = [
            os.path.join(repo_dir, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(repo_dir, 'subdir/subsubdir/poutrelle.xml'),
        ]

        expected_freezed = [
            os.path.join(repo_dir, 'file.txt'),
            os.path.join(repo_dir, 'file2.txt'),
            os.path.join(repo_dir, 'subdir/subfile.txt'),
            os.path.join(repo_dir, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(repo_dir, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(repo_dir, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(repo_dir, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_api_exclude_multiple(self, app, client):
        """
        Try to freeze a dir with an exclude rule
        """

        repo_dir = os.path.join('/repos/test_repo_freeze_exclude_multiple')

        self.set_old_atime(repo_dir, age=3600 * 5000)

        self.freeze_and_wait(client, repo_dir)

        not_expected_freezed = [
            os.path.join(repo_dir, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(repo_dir, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(repo_dir, 'subdir/subsubdir/poutrelle.tsv')
        ]

        expected_freezed = [
            os.path.join(repo_dir, 'file.txt'),
            os.path.join(repo_dir, 'file2.txt'),
            os.path.join(repo_dir, 'subdir/subfile.txt'),
            os.path.join(repo_dir, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(repo_dir, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(repo_dir, 'subdir/subsubdir/subsubfile.txt'),
        ]

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def freeze_quick(self, client, path, email=None):
        data = {
            'path': path
        }
        if email:
            data['email'] = email
        response = client.post('/freeze', json=data)

        assert response.status_code == 200
        assert 'task' in response.json

        return response.json['task']

    def wait_for_freeze(self, client, freeze_id):
        # Wait for the task to run
        wait = 0
        while wait < 10:
            sleep(2)

            response = client.get('/status/%s' % freeze_id)

            assert response.status_code == 200

            if response.json['task']['finished'] == "true":
                break
            else:
                assert response.json['task']['error'] == 'false'
            wait += 1

        assert response.json['task'] == {'finished': 'true', 'error': 'false', 'info': None}

    def freeze_and_wait(self, client, path):

        freeze_id = self.freeze_quick(client, path)
        self.wait_for_freeze(client, freeze_id)

# TODO [HI] better test for freezeing a dir when a subdir is already freezeing: multiple subdirs in parallel, timeout waiting
