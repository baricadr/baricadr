import os
import shutil

from . import BaricadrTestCase


class TestReposPull(BaricadrTestCase):

    template_repo = "/baricadr/test-data/test-repo/"
    testing_repo = "/repos/test_repo_freeze_tmp/"

    def setup_method(self):
        if os.path.exists(self.testing_repo):
            shutil.rmtree(self.testing_repo)

    def teardown_method(self):
        if os.path.exists(self.testing_repo):
            shutil.rmtree(self.testing_repo)

    def test_pull_success(self, app):

        conf = {
            self.testing_repo: {
                'backend': 'sftp',
                'url': 'sftp:test-repo/',
                'user': 'foo',
                'password': 'pass',
                'freeze_age': 3,
                'freezable': True
            }
        }

        app.repos.read_conf_from_str(str(conf))

        repo = app.repos.get_repo(self.testing_repo)
        pull_res = repo.pull(self.testing_repo)

        assert len(pull_res) == 2
        assert sorted(pull_res[0]) == sorted([
            'subdir/subfile.txt',
            'file.txt',
            'file2.txt',
            'subdir/subsubdir2/poutrelle.xml',
            'subdir/subsubdir2/subsubfile.txt',
            'subdir/subsubdir2/subsubsubdir/subsubsubdir2/a file',
            'subdir/subsubdir/subsubfile.txt',
            'subdir/subsubdir/poutrelle.tsv',
            'subdir/subsubdir/poutrelle.xml'
        ])
        assert pull_res[1] == 126
