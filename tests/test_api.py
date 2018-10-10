from . import app, client, BaricadTestCase


class TestApi(BaricadTestCase):

    def test_get_status_unknown(self, client):
        response = client.get('/status/foobar')

        # TODO maybe we should send a 404 error, but celery can't say if the task is finished or doesn't exist
        assert response.json == {'finished': False, 'info': None}
        assert response.status_code == 200
