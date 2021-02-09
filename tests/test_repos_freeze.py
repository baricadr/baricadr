import os
import shutil
from datetime import datetime

import pytest

from . import BaricadrTestCase


class TestReposFreeze(BaricadrTestCase):

    template_repo = "/baricadr/test-data/test-repo/"
    testing_repo = "/repos/test_repo_freeze_tmp/"

    def setup_method(self):
        if os.path.exists(self.testing_repo):
            shutil.rmtree(self.testing_repo)
        shutil.copytree(self.template_repo, self.testing_repo, symlinks=True, ignore_dangling_symlinks=True)

    def teardown_method(self):
        if os.path.exists(self.testing_repo):
            shutil.rmtree(self.testing_repo)

    def test_freeze_age_whole_dir(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        self.set_old_atime(self.testing_repo)

        freezed = repo.freeze(self.testing_repo)

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

        assert sorted(freezed) == sorted(expected_freezed)

    def test_freeze_age_subdir(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        self.set_old_atime(self.testing_repo)

        freezed = repo.freeze(os.path.join(self.testing_repo, 'subdir'))

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt')
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

        assert sorted(freezed) == sorted(expected_freezed)

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for not_exp_freezed in not_expected_freezed:
            assert os.path.exists(not_exp_freezed)

    def test_freeze_exclude(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'exclude': "*xml",
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        self.set_old_atime(self.testing_repo)

        expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
        ]

        for exp_freezed in expected_freezed:
            assert os.path.exists(exp_freezed)

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

        freezed = repo.freeze(self.testing_repo)

        assert sorted(freezed) == sorted(expected_freezed)

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

    def test_freeze_exclude_multiple(self, app):

        # First get a local repo

        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'exclude': "*xml , *tsv",
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        self.set_old_atime(self.testing_repo)

        expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt')
        ]

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for exp_freezed in expected_freezed:
            assert os.path.exists(exp_freezed)

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

        freezed = repo.freeze(self.testing_repo)

        assert sorted(freezed) == sorted(expected_freezed)

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

    def test_freeze_dry_run(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)
        repo.pull(self.testing_repo)

        self.set_old_atime(self.testing_repo)

        freezed = repo.freeze(self.testing_repo, dry_run=True)

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

        assert sorted(freezed) == sorted(expected_freezed)

        for exp_freezed in expected_freezed:
            assert os.path.exists(exp_freezed)

    def test_freeze_local_only(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        # Copy a local-only file in local repo
        copied_file = self.testing_repo + '/subdir/subfile.txt'
        local_file = self.testing_repo + '/subdir/local_new_file.txt'
        shutil.copyfile(copied_file, local_file)
        self.set_old_atime(self.testing_repo)
        assert os.path.exists(local_file)

        freezed = repo.freeze(self.testing_repo)

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

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/local_new_file.txt'),
        ]

        assert sorted(freezed) == sorted(expected_freezed)

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

        assert os.path.exists(local_file)

    def test_freeze_local_only_single(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        # Copy a local-only file in local repo
        copied_file = self.testing_repo + '/subdir/subfile.txt'
        local_file = self.testing_repo + '/subdir/local_new_file.txt'
        shutil.copyfile(copied_file, local_file)

        self.set_old_atime(copied_file, age=3600 * 500, recursive=False)
        self.set_old_atime(local_file, age=3600 * 500, recursive=False)

        assert os.path.exists(local_file)

        with pytest.raises(RuntimeError):
            # Trying to freeze a file unknown by baricadr => we expect an error
            repo.freeze(local_file)

    def test_freeze_mixed(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        self.set_old_atime(self.testing_repo)

        accessed_file = self.testing_repo + '/subdir/subsubdir2/subsubfile.txt'
        dt = datetime.today()  # Get timezone naive now
        now_time = dt.timestamp()
        os.utime(accessed_file, (now_time, now_time))

        freezed = repo.freeze(self.testing_repo)

        expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt')
        ]

        assert sorted(freezed) == sorted(expected_freezed)

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

    def test_non_freezable_repo(self, app):

        # First get a local repo

        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': False
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        self.set_old_atime(self.testing_repo)

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir/subfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

        freezed = repo.freeze(self.testing_repo)

        assert freezed == []

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

    def test_force_freeze(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        # Set old atime to subdir (should be ignored by force)
        repo = app.repos.get_repo(self.testing_repo)
        repo_dir = os.path.join(self.testing_repo, 'subdir')
        self.set_old_atime(repo_dir)

        # Modifiy both files with recent atime and old atime

        # File
        with open(os.path.join(self.testing_repo, 'file.txt'), 'r') as local_file:
            assert local_file.readline() == 'file content\n'

        with open(os.path.join(self.testing_repo, 'file.txt'), 'w') as local_file:
            local_file.write('This file was touched locally\n')

        # Subfile
        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'subfile content\n'

        with open(repo_dir + '/subfile.txt', 'w') as local_file:
            local_file.write('This subfile was touched locally\n')

        freezed = repo.freeze(self.testing_repo, force=True)

        expected_freezed = [
            os.path.join(self.testing_repo, 'file2.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/subsubfile.txt'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.xml'),
            os.path.join(self.testing_repo, 'subdir/subsubdir/poutrelle.tsv')
        ]

        not_expected_freezed = [
            os.path.join(self.testing_repo, 'file.txt'),
            os.path.join(self.testing_repo, 'subdir/subfile.txt')
        ]

        assert sorted(freezed) == sorted(expected_freezed)

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

        for nexp_freezed in not_expected_freezed:
            assert os.path.exists(nexp_freezed)

        with open(os.path.join(self.testing_repo, 'file.txt'), 'r') as local_file:
            assert local_file.readline() == 'This file was touched locally\n'

        with open(repo_dir + '/subfile.txt', 'r') as local_file:
            assert local_file.readline() == 'This subfile was touched locally\n'
