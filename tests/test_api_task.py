from . import BaricadrTestCase


class TestApiTask(BaricadrTestCase):

    def test_get_status_unknown(self, client):
        """
        Get status from a non-existing task
        """
        response = client.get('/tasks/status/foobar')

        # TODO maybe we should send a 404 error, but celery can't say if the task is finished or doesn't exist
        assert response.json['task'] == {'finished': 'false', 'error': 'false', 'info': None}
        assert response.status_code == 200

    def test_delete_unknown(self, client):
        """
            Try to delete a non existing task
        """
        response = client.get('/tasks/remove/foobar')
        assert response.json['error'] == "Task not found in Baricadr database."
        assert response.status_code == 200
