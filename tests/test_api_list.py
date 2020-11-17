import os
from pathlib import Path

from . import BaricadrTestCase


class TestApiList(BaricadrTestCase):

    def test_list_fill_depth_1(self, client):
        """
            Get files at depth 1
        """
        body = {"path": "/repos/test_repo/", "max_depth": 1}
        file_list = ["file.txt", "file2.txt"]
        response = client.post("/list", json=body)

        assert response.status_code == 200
        remote_file_list = set([file['Path'] for file in response.json])
        assert remote_file_list == set(file_list)

    def test_list_fill_depth_2(self, client):
        """
            Get files at depth 1
        """
        body = {"path": "/repos/test_repo/", "max_depth": 2}
        file_list = ["file.txt", "file2.txt", "subdir/subfile.txt"]
        response = client.post("/list", json=body)

        assert response.status_code == 200
        remote_file_list = set([file['Path'] for file in response.json])
        assert remote_file_list == set(file_list)

    def test_list_fill_max_depth(self, client):
        """
            Get files at depth 1
        """
        body = {"path": "/repos/test_repo/", "max_depth": 0}
        response = client.post("/list", json=body)

        assert response.status_code == 200
        assert len(response.json) == 9

    def test_list_fill_missing(self, client):
        """
            Get files at depth 1 and check missing
        """
        if not os.path.isfile("/repos/test_repo/file.txt"):
            Path("/repos/test_repo/file.txt").touch()
        if os.path.isfile("/repos/test_repo/file2.txt"):
            os.unlink("/repos/test_repo/file2.txt")

        body = {"path": "/repos/test_repo/", "missing": "True"}
        response = client.post("/list", json=body)

        assert response.status_code == 200
        remote_file_list = [file['Path'] for file in response.json]

        assert remote_file_list == ["file2.txt"]

    def test_get_status_unknown(self, client):
        """
        Get status from a non-existing task
        """
        response = client.get('/status/foobar')

        # TODO maybe we should send a 404 error, but celery can't say if the task is finished or doesn't exist
        assert response.json['task'] == {'finished': 'false', 'error': 'false', 'info': None}
        assert response.status_code == 200

# TODO [LOW] test checksum
# TODO [LOW] document how to run backups: disable --delete mode!! + how to handle moved data (not a problem with archive)?
# TODO [LOW] readthedocs for cli
