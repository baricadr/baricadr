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

    def test_list_full(self, client):
        """
            Get files with full info
        """
        body = {"path": "/repos/test_repo/", 'full': True}
        response = client.post("/list", json=body)

        assert response.status_code == 200
        assert len(response.json) == 2

        # Not checking mtime since we do not know what to expect
        expected = [
            {
                "IsDir": False,
                "MimeType": "text/plain; charset=utf-8",
                "Name": "file.txt",
                "Path": "file.txt",
                "Size": 13
            },
            {
                "IsDir": False,
                "MimeType": "text/plain; charset=utf-8",
                "Name": "file2.txt",
                "Path": "file2.txt",
                "Size": 8
            }
        ]

        keys = ["IsDir", "MimeType", "ModTime", "Name", "Size", "Path"]
        for file in response.json:
            assert all(key in file for key in keys)
            file.pop('ModTime', None)

        assert sorted(expected, key=lambda k: k['Path']) == sorted(response.json, key=lambda k: k['Path'])


# TODO document how to run backups: disable --delete mode!! + how to handle moved data (not a problem with archive)?
# TODO readthedocs for barique
# TODO secure api access (if need be)
# TODO secure barique credentials
# TODO quay.io images
# TODO pypi barique
# TODO proper release
