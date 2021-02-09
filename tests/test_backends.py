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
            assert os.path.isfile(single_file)

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
            assert os.path.isfile(single_file)

    def test_pull_sftp_single_invalid(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/non_existing_file.txt'

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
            with pytest.raises(RuntimeError):
                repo.pull(single_file)

            assert not os.path.exists(single_file)

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
            assert os.path.isfile(single_file + '/subfile.txt')
            assert os.path.isdir(single_file + '/subsubdir')
            assert os.path.exists(single_file + '/subsubdir/subsubfile.txt')
            assert os.path.isfile(single_file + '/subsubdir/subsubfile.txt')

            # Spaces
            assert os.path.exists(single_file + '/subsubdir2/subsubsubdir/subsubsubdir2/a file')
            assert os.path.isfile(single_file + '/subsubdir2/subsubsubdir/subsubsubdir2/a file')

    def test_pull_sftp_repo_invalid(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/non_existing_subdir/'

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

            with pytest.raises(RuntimeError):
                repo.pull(single_file)

            assert not os.path.exists(single_file + '/subfile.txt')

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
            assert os.path.isfile(single_file + '/subfile.txt')
            assert os.path.isdir(single_file + '/subsubdir')
            assert os.path.exists(single_file + '/subsubdir/subsubfile.txt')
            assert os.path.isfile(single_file + '/subsubdir/subsubfile.txt')

    def test_remote_is_single_sftp_single_file(self, app):

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
            assert repo.remote_is_single(single_file)

    def test_remote_is_single_sftp_single2(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file'

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
            assert repo.remote_is_single(single_file)

    def test_remote_is_single_sftp_multi(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/subdir/'

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
            assert not repo.remote_is_single(single_file)

    def test_remote_is_single_sftp_single_dir(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/subdir/subsubdir2/subsubsubdir/subsubsubdir2/'

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
            assert repo.remote_is_single(single_file)

    def test_remote_list_sftp(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            target = local_path + '/subdir/'

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass'
                }
            }

            app.repos.read_conf_from_str(str(conf))
            repo = app.repos.get_repo(target)

            # Order is unreliable, compare sets
            assert set([file['Path'] for file in repo.remote_list(target, max_depth=2)]) == set([
                'subfile.txt',
                'subsubdir/absolute_symlink.tsv',
                'subsubdir/relative_symlink.tsv',
                'subsubdir2/poutrelle.xml',
                'subsubdir2/subsubfile.txt',
                'subsubdir/poutrelle.tsv',
                'subsubdir/poutrelle.xml',
                'subsubdir/subsubfile.txt',
            ])

    def test_remote_list_sftp_full(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            target = local_path + '/subdir/'

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass'
                }
            }

            app.repos.read_conf_from_str(str(conf))
            repo = app.repos.get_repo(target)

            # Order is unreliable, compare sets
            assert set([file['Path'] for file in repo.remote_list(target, max_depth=0)]) == set([
                'subfile.txt',
                'subsubdir/absolute_symlink.tsv',
                'subsubdir/relative_symlink.tsv',
                'subsubdir2/poutrelle.xml',
                'subsubdir2/subsubfile.txt',
                'subsubdir2/subsubsubdir/subsubsubdir2/a file',
                'subsubdir/poutrelle.tsv',
                'subsubdir/poutrelle.xml',
                'subsubdir/subsubfile.txt',
            ])
