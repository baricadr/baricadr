import os
import shutil
from time import sleep

from . import BaricadrTestCase


class TestApiPull(BaricadrTestCase):

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

    def test_pull_single(self, app, client):
        """
        Try to pull a file in normal conditions
        """

        repo_file = '/repos/test_repo/subdir/subfile.txt'
        if os.path.exists(repo_file):
            shutil.rmtree(repo_file)

        self.pull_and_wait(client, repo_file)

        assert os.path.exists(repo_file + '/subfile.txt')

        if os.path.exists(repo_file):
            shutil.rmtree(repo_file)

    def test_pull_single_non_excluded(self, app, client):
        """
        Try to pull a file in normal conditions, with excludes but not for asked file
        """

        repo_file = '/repos/test_repo_exclude/subdir/subfile.txt'
        if os.path.exists(repo_file):
            shutil.rmtree(repo_file)

        self.pull_and_wait(client, repo_file)

        assert os.path.exists(repo_file + '/subfile.txt')

        if os.path.exists(repo_file):
            shutil.rmtree(repo_file)

    def test_pull_single_excluded(self, app, client):
        """
        Try to pull a file in normal conditions, with excluded file
        """

        repo_file = '/repos/test_repo_exclude/subdir/subfile.txt'
        if os.path.exists(repo_file):
            shutil.rmtree(repo_file)

        self.pull_and_wait(client, repo_file)

        assert os.path.exists(repo_file + '/subsubdir/poutrelle.xml')

        if os.path.exists(repo_file):
            shutil.rmtree(repo_file)

    def test_pull_rclone_symlinks(self, app, client):
        """
        Try to pull a dir containing symlinks in rclone format
        """

        repo_dir = '/repos/test_repo_sftp/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        # Check relative symlinks
        assert os.path.exists(repo_dir + '/subsubdir/relative_symlink.tsv')
        assert os.path.islink(repo_dir + '/subsubdir/relative_symlink.tsv')
        assert os.readlink(repo_dir + '/subsubdir/relative_symlink.tsv') == 'poutrelle.tsv'

        # Check absolute, dangling symlinks
        assert os.path.islink(repo_dir + '/subsubdir/absolute_symlink.tsv')
        assert os.readlink(repo_dir + '/subsubdir/absolute_symlink.tsv') == '/tmp/something.tsv'

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_rclone_symlinks_existing_same(self, app, client):
        """
        Try to pull a dir containing symlinks in rclone format, with a preexisting symlink
        """

        repo_dir = '/repos/test_repo_sftp/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        os.makedirs(repo_dir + '/subsubdir/')
        os.symlink('poutrelle.tsv', repo_dir + '/subsubdir/relative_symlink.tsv')
        os.symlink('/tmp/something.tsv', repo_dir + '/subsubdir/absolute_symlink.tsv')

        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        # Check relative symlinks
        assert os.path.exists(repo_dir + '/subsubdir/relative_symlink.tsv')
        assert os.path.islink(repo_dir + '/subsubdir/relative_symlink.tsv')
        assert os.readlink(repo_dir + '/subsubdir/relative_symlink.tsv') == 'poutrelle.tsv'

        # Check absolute, dangling symlinks
        assert os.path.islink(repo_dir + '/subsubdir/absolute_symlink.tsv')
        assert os.readlink(repo_dir + '/subsubdir/absolute_symlink.tsv') == '/tmp/something.tsv'

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_rclone_symlinks_existing_diff(self, app, client):
        """
        Try to pull a dir containing symlinks in rclone format, with a preexisting different symlink
        """

        repo_dir = '/repos/test_repo_sftp/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        os.makedirs(repo_dir + '/subsubdir/')
        os.symlink('poutrellexx.tsv', repo_dir + '/subsubdir/relative_symlink.tsv')
        os.symlink('/tmp/somethingxx.tsv', repo_dir + '/subsubdir/absolute_symlink.tsv')

        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        # Check relative symlinks
        assert os.path.islink(repo_dir + '/subsubdir/relative_symlink.tsv')
        assert os.readlink(repo_dir + '/subsubdir/relative_symlink.tsv') == 'poutrellexx.tsv'

        # Check absolute, dangling symlinks
        assert os.path.islink(repo_dir + '/subsubdir/absolute_symlink.tsv')
        assert os.readlink(repo_dir + '/subsubdir/absolute_symlink.tsv') == '/tmp/somethingxx.tsv'

        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    def test_pull_rclone_symlinks_existing_file(self, app, client):
        """
        Try to pull a dir containing symlinks in rclone format, with a preexisting file instead of symlink

        In this case rclone will replace local files with remote symlinks.
        """

        repo_dir = '/repos/test_repo_sftp/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        os.makedirs(repo_dir + '/subsubdir/')

        with open(repo_dir + '/subsubdir/relative_symlink.tsv', 'w') as local_file:
            local_file.write('This was touched locally\n')
        with open(repo_dir + '/subsubdir/absolute_symlink.tsv', 'w') as local_file:
            local_file.write('This was touched locally\n')

        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        # Check relative symlinks
        assert os.path.islink(repo_dir + '/subsubdir/relative_symlink.tsv')
        assert os.readlink(repo_dir + '/subsubdir/relative_symlink.tsv') == 'poutrelle.tsv'

        # Check absolute, dangling symlinks
        assert os.path.islink(repo_dir + '/subsubdir/absolute_symlink.tsv')
        assert os.readlink(repo_dir + '/subsubdir/absolute_symlink.tsv') == '/tmp/something.tsv'

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
        self.wait_for_pull(client, pull_id)
        self.wait_for_pull(client, pull_id_2)

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
        self.wait_for_pull(client, pull_id)
        self.wait_for_pull(client, pull_id_2)

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

    def test_pull_race_multiple(self, app, client):
        """
        Try to pull multiple dirs at the same time
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        pull_id = self.pull_quick(client, repo_dir + '/subsubdir2')
        pull_id_2 = self.pull_quick(client, repo_dir + '/subsubdir2/subsubsubdir')
        pull_id_3 = self.pull_quick(client, repo_dir + '/subsubdir2/subsubsubdir/subsubsubdir2')
        pull_id_4 = self.pull_quick(client, repo_dir + '/subsubdir2/poutrelle.xml')

        # Some pull_ids will be identical depending on timing

        # Wait for the tasks to run
        self.wait_for_pull(client, pull_id)
        self.wait_for_pull(client, pull_id_2)
        self.wait_for_pull(client, pull_id_3)
        self.wait_for_pull(client, pull_id_4)

        assert not os.path.exists(repo_dir + '/subfile.txt')

        assert not os.path.isdir(repo_dir + '/subsubdir')
        assert not os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert not os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')
        assert not os.path.exists(repo_dir + '/subsubdir/poutrelle.tsv')

        assert os.path.isdir(repo_dir + '/subsubdir2')
        assert os.path.exists(repo_dir + '/subsubdir2/subsubfile.txt')
        assert os.path.exists(repo_dir + '/subsubdir2/poutrelle.xml')
        assert os.path.isdir(repo_dir + '/subsubdir2/subsubsubdir')
        assert os.path.isdir(repo_dir + '/subsubdir2/subsubsubdir/subsubsubdir2')
        assert os.path.exists(repo_dir + '/subsubdir2/subsubsubdir/subsubsubdir2/a file')

        assert not os.path.exists(repo_dir + '../file.txt')
        assert not os.path.exists(repo_dir + '../file2.txt')

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
        Try to pull a dir containing some file modified locally a long time ago
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

        self.set_old_atime(repo_dir + '/subfile.txt', age=3600 * 30000, recursive=False)

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

    def test_pull_chown(self, app, client):
        """
        Try to pull a dir in normal conditions and check chown
        """

        repo_dir = '/repos/test_repo/subdir'
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        self.pull_and_wait(client, repo_dir)

        assert os.path.exists(repo_dir + '/subfile.txt')
        assert os.path.isdir(repo_dir + '/subsubdir')
        assert os.path.exists(repo_dir + '/subsubdir/subsubfile.txt')
        assert os.path.exists(repo_dir + '/subsubdir/poutrelle.xml')

        # Check owner
        assert os.stat(repo_dir + '/subfile.txt').st_uid == 9876
        assert os.stat(repo_dir + '/subfile.txt').st_gid == 9786
        assert os.stat(repo_dir + '/subsubdir').st_uid == 9876
        assert os.stat(repo_dir + '/subsubdir').st_gid == 9786
        assert os.stat(repo_dir + '/subsubdir/subsubfile.txt').st_uid == 9876
        assert os.stat(repo_dir + '/subsubdir/subsubfile.txt').st_gid == 9786
        assert os.stat(repo_dir + '/subsubdir/subsubfile.txt').st_uid == 9876
        assert os.stat(repo_dir + '/subsubdir/subsubfile.txt').st_gid == 9786
        assert os.stat(repo_dir + '/subsubdir2/subsubsubdir').st_uid == 9876
        assert os.stat(repo_dir + '/subsubdir2/subsubsubdir').st_gid == 9786

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
        while wait < 30:
            sleep(2)

            response = client.get('/tasks/status/%s' % pull_id)

            assert response.status_code == 200

            if response.json['status'] == "finished":
                break
            else:
                assert not response.json['error']
            wait += 1

        assert response.json['status'] == "finished"
        assert not response.json['error']

    def pull_and_wait(self, client, path):

        pull_id = self.pull_quick(client, path)
        self.wait_for_pull(client, pull_id)
