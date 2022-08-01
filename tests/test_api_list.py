import os
from pathlib import Path

from . import BaricadrTestCase


class TestApiList(BaricadrTestCase):

    repo_root = "/repos/test_repo/"
    expected_mimetype = "text/plain; charset=utf-8"

    def test_list_wrong_repo(self, client):
        """
            Get files at depth 1
        """
        body = {"path": "/blabla"}
        response = client.post("/list", json=body)

        assert response.status_code == 400
        assert response.json['error'] == "Could not find baricadr repository for path /blabla"

    def test_list_fill_depth_1(self, client):
        """
            Get files at depth 1
        """
        body = {"path": self.repo_root, "max_depth": 1}
        file_list = ["file.txt", "file2.txt"]
        response = client.post("/list", json=body)

        assert response.status_code == 200
        remote_file_list = set([file['Path'] for file in response.json])
        assert remote_file_list == set(file_list)

    def test_list_fill_depth_2(self, client):
        """
            Get files at depth 1
        """
        body = {"path": self.repo_root, "max_depth": 2}
        file_list = ["file.txt", "file2.txt", "subdir/subfile.txt"]
        response = client.post("/list", json=body)

        assert response.status_code == 200
        remote_file_list = set([file['Path'] for file in response.json])
        assert remote_file_list == set(file_list)

    def test_list_fill_max_depth(self, client):
        """
            Get files at depth 1
        """
        body = {"path": self.repo_root, "max_depth": 0}
        response = client.post("/list", json=body)

        assert response.status_code == 200
        assert len(response.json) == 9

    def test_list_fill_missing(self, client):
        """
            Get files at depth 1 and check missing
        """
        if not os.path.isfile(os.path.join(self.repo_root, "file.txt")):
            Path(os.path.join(self.repo_root, "file.txt")).touch()
        if os.path.isfile(os.path.join(self.repo_root, "file2.txt")):
            os.unlink(os.path.join(self.repo_root, "file2.txt"))

        body = {"path": self.repo_root, "missing": "True"}
        response = client.post("/list", json=body)

        assert response.status_code == 200
        remote_file_list = [file['Path'] for file in response.json]

        assert remote_file_list == ["file2.txt"]

    def test_list_full(self, client):
        """
            Get files with full info
        """
        body = {"path": self.repo_root, 'full': True}
        response = client.post("/list", json=body)

        assert response.status_code == 200
        assert len(response.json) == 2

        # Not checking mtime since we do not know what to expect
        expected = [
            {
                "IsDir": False,
                "MimeType": self.expected_mimetype,
                "Name": "file.txt",
                "Path": "file.txt",
                "Size": 13
            },
            {
                "IsDir": False,
                "MimeType": self.expected_mimetype,
                "Name": "file2.txt",
                "Path": "file2.txt",
                "Size": 8
            }
        ]

        keys = ["IsDir", "MimeType", "ModTime", "Name", "Size", "Path"]
        received = []
        for file in response.json:
            assert all(key in file for key in keys)
            file.pop('ModTime', None)
            file.pop('Tier', None)
            received.append(file)

        assert sorted(expected, key=lambda k: k['Path']) == sorted(received, key=lambda k: k['Path'])


class TestApiListS3(TestApiList):
    """
    Same tests, but with S3
    """

    repo_root = "/repos/test_repo_s3/"
    expected_mimetype = "text/plain"
