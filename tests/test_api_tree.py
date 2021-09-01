import os
from pathlib import Path

from . import BaricadrTestCase


class TestApiList(BaricadrTestCase):

    repo_root = "/repos/test_repo/"
    expected_mimetype = "text/plain; charset=utf-8"

    def test_tree_depth_1(self, client):
        """
            Get files at depth 1
        """
        body = {"path": self.repo_root, "max_depth": 1}
        file_list = ["file.txt", "file2.txt"]
        response = client.post("/tree", json=body)

        assert response.status_code == 200
        remote_file_list = set([file['Path'] for file in response.json])
        assert remote_file_list == set(file_list)

    def test_tree_depth_2(self, client):
        """
            Get files at depth 1
        """
        body = {"path": self.repo_root, "max_depth": 2}
        file_list = ["file.txt", "file2.txt", "subdir/subfile.txt"]
        response = client.post("/tree", json=body)

        assert response.status_code == 200
        remote_file_list = set([file['Path'] for file in response.json])
        assert remote_file_list == set(file_list)

    def test_tree_max_depth(self, client):
        """
            Get files at depth 1
        """
        body = {"path": self.repo_root, "max_depth": 0}
        response = client.post("/tree", json=body)

        assert response.status_code == 200
        assert len(response.json) == 9

    def test_tree_missing(self, client):
        if not os.path.isfile(os.path.join(self.repo_root, "file.txt")):
            Path(os.path.join(self.repo_root, "file.txt")).touch()
        if os.path.isfile(os.path.join(self.repo_root, "file2.txt")):
            os.unlink(os.path.join(self.repo_root, "file2.txt"))

        body = {"path": self.repo_root}
        response = client.post("/tree", json=body)

        assert response.status_code == 200
        remote_file_list = [file['Path'] for file in response.json]

        assert remote_file_list == ["file.txt", "file2.txt*"]


class TestApiListS3(TestApiList):
    """
    Same tests, but with S3
    """

    repo_root = "/repos/test_repo_s3/"
    expected_mimetype = "text/plain"
