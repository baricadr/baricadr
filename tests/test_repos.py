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
                'freezable': True,
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
                'freezable': True,
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
                'freezable': True
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
                'freezable': True,
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
                'freezable': True,
                'freeze_age': 100000
            },
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_chown_uid_conf(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
                'chown_uid': 4586,
            },
        }

        repos = app.repos.do_read_conf(str(conf))
        repo = repos['/foo/bar']
        assert repo.chown_uid == 4586

    def test_chown_uid_conf_too_big(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
                'chown_uid': 100000,
            },
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))

    def test_chown_gid_conf(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
                'chown_gid': 4586,
            },
        }

        repos = app.repos.do_read_conf(str(conf))
        repo = repos['/foo/bar']
        assert repo.chown_gid == 4586

    def test_chown_gid_conf_too_big(self, app):
        conf = {
            '/foo/bar': {
                'backend': 's3',
                'url': 'google',
                'user': 'someone',
                'password': 'xxxxx',
                'chown_gid': 100000,
            },
        }

        with pytest.raises(ValueError):
            app.repos.do_read_conf(str(conf))
