import os
from pathlib import Path

from . import BaricadrTestCase


class TestApiList(BaricadrTestCase):

    repo_root = "/repos/test_repo/"
    expected_mimetype = "text/plain; charset=utf-8"

    def test_tree_missing(self, client):
        if not os.path.isfile(os.path.join(self.repo_root, "file.txt")):
            Path(os.path.join(self.repo_root, "file.txt")).touch()
        if os.path.isfile(os.path.join(self.repo_root, "file2.txt")):
            os.unlink(os.path.join(self.repo_root, "file2.txt"))

        body = {"path": self.repo_root}
        response = client.post("/tree", json=body)

        assert response.status_code == 200
        remote_file_list = [file['Path'] for file in response.json]

        assert sorted(remote_file_list) == sorted(["file.txt", "file2.txt*"])


class TestApiListS3(TestApiList):
    """
    Same tests, but with S3
    """

    repo_root = "/repos/test_repo_s3/"
    expected_mimetype = "text/plain"
