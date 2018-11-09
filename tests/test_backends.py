import os
import tempfile

import pytest

from . import BaricadrTestCase


class TestBackends(BaricadrTestCase):

    def test_get(self, app):
        conf = {
            'url': 'foo:/some/where',
            'user': 'foo',
            'password': 'pass'
        }
        be = app.backends.get_by_name("sftp", conf)

        assert be.__class__.__name__ == 'SftpBackend'

    def test_get_empty_conf(self, app):
        conf = {}
        with pytest.raises(ValueError):
            app.backends.get_by_name("sftp", conf)

        conf = {
            'url': 'foo:/some/where',
        }
        with pytest.raises(ValueError):
            app.backends.get_by_name("sftp", conf)

        conf = {
            'url': 'foo:/some/where',
            'user': 'foo',
        }
        with pytest.raises(ValueError):
            app.backends.get_by_name("sftp", conf)

    def test_pull_sftp_single(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/file.txt'

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass'
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(single_file)
            repo.pull(single_file)

            assert os.path.exists(single_file)

    def test_pull_sftp_single_no_slash(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/file.txt'

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo',
                    'user': 'foo',
                    'password': 'pass'
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(single_file)
            repo.pull(single_file)

            assert os.path.exists(single_file)

    def test_pull_sftp_repo(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/subdir/'

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo',
                    'user': 'foo',
                    'password': 'pass'
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(single_file)
            repo.pull(single_file)
            assert os.path.exists(single_file + '/subfile.txt')
            assert os.path.isdir(single_file + '/subsubdir')
            assert os.path.exists(single_file + '/subsubdir/subsubfile.txt')

    def test_pull_sftp_repo_no_slash(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/subdir'

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo',
                    'user': 'foo',
                    'password': 'pass'
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(single_file)
            repo.pull(single_file)
            assert os.path.exists(single_file + '/subfile.txt')
            assert os.path.isdir(single_file + '/subsubdir')
            assert os.path.exists(single_file + '/subsubdir/subsubfile.txt')
