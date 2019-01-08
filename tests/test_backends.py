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
            assert repo.remote_list(target) == [
                'subfile.txt',
                'subsubdir2/poutrelle.xml',
                'subsubdir2/subsubfile.txt',
                'subsubdir2/subsubsubdir/subsubsubdir2/a file',
                'subsubdir/poutrelle.tsv',
                'subsubdir/poutrelle.xml',
                'subsubdir/subsubfile.txt',
            ]

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
            remote_list = []
            for rli in repo.remote_list(target, True):
                del rli['ModTime']  # ModTime is too hard to test properly
                remote_list.append(rli)
            assert remote_list == [{'Path': 'subfile.txt', 'Name': 'subfile.txt', 'Size': 16, 'MimeType': 'text/plain; charset=utf-8', 'IsDir': False}, {'Path': 'subsubdir', 'Name': 'subsubdir', 'Size': -1, 'MimeType': 'inode/directory', 'IsDir': True}, {'Path': 'subsubdir2', 'Name': 'subsubdir2', 'Size': -1, 'MimeType': 'inode/directory', 'IsDir': True}, {'Path': 'subsubdir2/poutrelle.xml', 'Name': 'poutrelle.xml', 'Size': 13, 'MimeType': 'text/xml; charset=utf-8', 'IsDir': False}, {'Path': 'subsubdir2/subsubfile.txt', 'Name': 'subsubfile.txt', 'Size': 19, 'MimeType': 'text/plain; charset=utf-8', 'IsDir': False}, {'Path': 'subsubdir2/subsubsubdir', 'Name': 'subsubsubdir', 'Size': -1, 'MimeType': 'inode/directory', 'IsDir': True}, {'Path': 'subsubdir2/subsubsubdir/subsubsubdir2', 'Name': 'subsubsubdir2', 'Size': -1, 'MimeType': 'inode/directory', 'IsDir': True}, {'Path': 'subsubdir2/subsubsubdir/subsubsubdir2/a file', 'Name': 'a file', 'Size': 0, 'MimeType': 'application/octet-stream', 'IsDir': False}, {'Path': 'subsubdir/poutrelle.tsv', 'Name': 'poutrelle.tsv', 'Size': 25, 'MimeType': 'text/tab-separated-values; charset=utf-8', 'IsDir': False}, {'Path': 'subsubdir/poutrelle.xml', 'Name': 'poutrelle.xml', 'Size': 13, 'MimeType': 'text/xml; charset=utf-8', 'IsDir': False}, {'Path': 'subsubdir/subsubfile.txt', 'Name': 'subsubfile.txt', 'Size': 19, 'MimeType': 'text/plain; charset=utf-8', 'IsDir': False}]
