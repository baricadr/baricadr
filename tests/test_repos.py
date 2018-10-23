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

    def test_overlap2(self, app):
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
