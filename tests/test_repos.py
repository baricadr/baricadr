import os
import tempfile

import pytest

from . import BaricadrTestCase


class TestRepos(BaricadrTestCase):

    def test_get_empty(self, app):
        conf = {
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_get_incomplete(self, app):
        conf = {
            '/foo/bar': []
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_overlap(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx'
            },
            '/foo/bar/some/thing': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx'
            }
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_overlap_reverse(self, app):
        conf = {
            '/foo/bar/some/thing': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx'
            },
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx'
            }
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_overlap_symlink(self, app):

        lnk_src = '/foo/bar/some/thing'
        lnk_dst = '/tmp/somelink'

        if os.path.isdir(lnk_dst):
            os.unlink(lnk_dst)
        os.symlink(lnk_src, lnk_dst)

        conf = {
            '/foo/bar/': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx'
            },
            lnk_dst: {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx'
            }
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

        os.unlink(lnk_dst)

    def test_dir_not_exist(self, app):

        with tempfile.TemporaryDirectory() as local_path:
            local_path_not_exist = local_path + '/test/'
            conf = {
                local_path_not_exist: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass'
                }
            }

            assert not os.path.exists(local_path_not_exist)

            app.repos.read_conf_from_str(str(conf))

            assert os.path.exists(local_path_not_exist)

    def test_freeze_age_conf(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
                'freeze_age': 12
            },
        }

        repos = app.repos.do_read_conf(str(conf))
        repo = repos['/foo/bar']
        assert repo.freeze_age == 12

    def test_freeze_age_conf_str(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
                'freeze_age': 'xxxx'
            },
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_freeze_age_conf_none(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
            },
        }

        repos = app.repos.do_read_conf(str(conf))
        repo = repos['/foo/bar']
        assert repo.freeze_age == 180

    def test_freeze_age_conf_small(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
                'freeze_age': 1
            },
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_freeze_age_conf_big(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
                'freeze_age': 100000
            },
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_freeze_age_single_file(self, app):

        # First get a local repo
        with tempfile.TemporaryDirectory() as local_path:
            single_file = local_path + '/file.txt'

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass',
                    'freeze_age': 3
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(single_file)
            repo.pull(single_file)

            assert os.path.exists(local_path + '/file.txt')

            freezed = repo.freeze(local_path)

            assert freezed == [
                local_path + '/file.txt'
            ]

            assert not os.path.exists(local_path + '/file.txt')

            freezed = repo.freeze(single_file)

            assert freezed == []

            assert not os.path.exists(local_path + '/file.txt')

    def test_freeze_age_whole_dir(self, app):

        # First get a local repo
        with tempfile.TemporaryDirectory() as local_path:
            whole_dir = local_path

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass',
                    'freeze_age': 3
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(whole_dir)
            repo.pull(whole_dir)

            freezed = repo.freeze(local_path)

            expected_freezed = [
                local_path + '/file.txt',
                local_path + '/file2.txt',
                local_path + '/subdir/subfile.txt',
                local_path + '/subdir/subsubdir2/subsubfile.txt',
                local_path + '/subdir/subsubdir2/poutrelle.xml',
                local_path + '/subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file',
                local_path + '/subdir/subsubdir/subsubfile.txt',
                local_path + '/subdir/subsubdir/poutrelle.xml',
                local_path + '/subdir/subsubdir/poutrelle.tsv'
            ]

            assert freezed == expected_freezed

            for exp_freezed in expected_freezed:
                assert not os.path.exists(exp_freezed)

    def test_freeze_exclude(self, app):

        # First get a local repo
        with tempfile.TemporaryDirectory() as local_path:
            whole_dir = local_path

            # Don't exclude yet as we want to pull all files for the test
            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass',
                    'freeze_age': 3,
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(whole_dir)
            repo.pull(whole_dir)

            expected_freezed = [
                local_path + '/file.txt',
                local_path + '/file2.txt',
                local_path + '/subdir/subfile.txt',
                local_path + '/subdir/subsubdir2/subsubfile.txt',
                local_path + '/subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file',
                local_path + '/subdir/subsubdir/subsubfile.txt',
                local_path + '/subdir/subsubdir/poutrelle.tsv'
            ]

            not_expected_freezed = [
                local_path + '/subdir/subsubdir2/poutrelle.xml',
                local_path + '/subdir/subsubdir/poutrelle.xml',
            ]

            for exp_freezed in expected_freezed:
                assert os.path.exists(exp_freezed)

            for nexp_freezed in not_expected_freezed:
                assert os.path.exists(nexp_freezed)

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass',
                    'freeze_age': 3,
                    'exclude': "*xml"
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(whole_dir)

            freezed = repo.freeze(local_path)

            assert freezed == expected_freezed

            for exp_freezed in expected_freezed:
                assert not os.path.exists(exp_freezed)

            for nexp_freezed in not_expected_freezed:
                assert os.path.exists(nexp_freezed)

    def test_freeze_exclude_multiple(self, app):

        # First get a local repo
        with tempfile.TemporaryDirectory() as local_path:
            whole_dir = local_path

            # Don't exclude yet as we want to pull all files for the test
            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass',
                    'freeze_age': 3,
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(whole_dir)
            repo.pull(whole_dir)

            expected_freezed = [
                local_path + '/file.txt',
                local_path + '/file2.txt',
                local_path + '/subdir/subfile.txt',
                local_path + '/subdir/subsubdir2/subsubfile.txt',
                local_path + '/subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file',
                local_path + '/subdir/subsubdir/subsubfile.txt',
            ]

            not_expected_freezed = [
                local_path + '/subdir/subsubdir2/poutrelle.xml',
                local_path + '/subdir/subsubdir/poutrelle.xml',
                local_path + '/subdir/subsubdir/poutrelle.tsv'
            ]

            for exp_freezed in expected_freezed:
                assert os.path.exists(exp_freezed)

            for nexp_freezed in not_expected_freezed:
                assert os.path.exists(nexp_freezed)

            conf = {
                local_path: {
                    'backend': 'sftp',
                    'url': 'sftp:test-repo/',
                    'user': 'foo',
                    'password': 'pass',
                    'freeze_age': 3,
                    'exclude': "*xml , *tsv"
                }
            }

            app.repos.read_conf_from_str(str(conf))

            repo = app.repos.get_repo(whole_dir)

            freezed = repo.freeze(local_path)

            assert freezed == expected_freezed

            for exp_freezed in expected_freezed:
                assert not os.path.exists(exp_freezed)

            for nexp_freezed in not_expected_freezed:
                assert os.path.exists(nexp_freezed)
