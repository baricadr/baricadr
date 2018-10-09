import os.path
from flask import current_app
import yaml


class Repo():

    def __init__(self, local_path, conf):

        self.local_path = local_path
        self.exclude = None
        if 'exclude' in conf:
            self.exclude = conf['exclude']
        self.conf = conf

        self.backend = current_app.backends.get_by_name(conf['backend'], conf)

    def is_in_repo(self, path):
        return path.startswith(self.local_path)

    def pull(self, path):
        self.backend.pull(self, path)


class Repos():

    def __init__(self, config_file, backends):

        self.config_file = config_file
        self.backends = backends

        self.read_conf(config_file)

    def read_conf(self, path):

        # TODO check path existence
        self.repos = {}
        with open(path, 'r') as stream:
            repos_conf = yaml.safe_load(stream)
            for repo in repos_conf:
                repo_abs = os.path.abspath(repo)
                if repo_abs in self.repos:
                    raise RuntimeError('Could not load duplicate repository for path "%s"' % repo_abs)

                self.repos[repo_abs] = Repo(repo_abs, repos_conf[repo])

    def get_repo(self, path):

        for x in self.repos:
            if self.repos['x'].is_in_repo(path):
                return self.repos['x']

        raise RuntimeError('Could not find baricadr repository for path "%s"' % path)
