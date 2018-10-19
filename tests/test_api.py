from . import app, client, BaricadrTestCase


class TestApi(BaricadrTestCase):

    def test_pull_missing_path(self, client):
        data = {
            'files': '/foo/bar'
        }
        response = client.post('/pull', json=data)

        assert response.status_code == 400
        assert response.json == {'error': 'Missing "path"'}

    def test_pull_wrong_email(self, client):
        data = {
            'path': '/foo/bar',
            'email': 'x'
        }
        response = client.post('/pull', json=data)

        assert response.status_code == 400
        assert response.json == {"error": "The email address is not valid. It must have exactly one @-sign."}

    def test_get_status_unknown(self, client):
        response = client.get('/status/foobar')

        # TODO maybe we should send a 404 error, but celery can't say if the task is finished or doesn't exist
        assert response.json == {'finished': False, 'info': None}
        assert response.status_code == 200
