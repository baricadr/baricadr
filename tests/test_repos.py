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
