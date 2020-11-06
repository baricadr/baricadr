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
        shutil.copytree(self.template_repo, self.testing_repo)

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
                'freeze_age': 3
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

        assert sorted(freezed) == sorted(expected_freezed)

        for exp_freezed in expected_freezed:
            assert not os.path.exists(exp_freezed)

    def test_freeze_age_subdir(self, app):

        # First get a local repo
        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3
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
                'exclude': "*xml"
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
                'exclude': "*xml , *tsv"
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
                'freeze_age': 3
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
                'freeze_age': 3
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
                'freeze_age': 3
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)

        # Copy a local-only file in local repo
        copied_file = self.testing_repo + '/subdir/subfile.txt'
        local_file = self.testing_repo + '/subdir/local_new_file.txt'
        old_time = os.stat(copied_file).st_atime - (500 * 3600)
        shutil.copyfile(copied_file, local_file)
        os.utime(copied_file, (old_time, old_time))
        os.utime(local_file, (old_time, old_time))
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
                'freeze_age': 3
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