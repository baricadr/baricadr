import os.path
from flask import current_app
import yaml


class Repo():

    def __init__(self, local_path, conf):

        if 'backend' not in conf:
            raise ValueError("Malformed repository definition, missing backend '%s'" % conf)

        self.local_path = local_path  # No trailing slash
        self.exclude = None
        if 'exclude' in conf:
            self.exclude = conf['exclude']
        self.conf = conf

        self.backend = current_app.backends.get_by_name(conf['backend'], conf)

    def is_in_repo(self, path):
        return path.startswith(self.local_path)

    def pull(self, path):
        self.backend.pull(self, path)

    def relative_path(self, path):
        return path[len(self.local_path) + 1:]


class Repos():

    def __init__(self, config_file, backends):

        self.config_file = config_file
        self.backends = backends

        self.read_conf(config_file)

    def read_conf(self, path):

        # TODO check path existence
        with open(path, 'r') as stream:
            self.repos = self.do_read_conf(stream.read())

    def read_conf_from_str(self, content):

        self.repos = self.do_read_conf(content)

    def do_read_conf(self, content):

        # TODO check path existence
        repos = {}
        repos_conf = yaml.safe_load(content)
        if not repos_conf:
            raise ValueError("Malformed repository definition '%s'" % content)

        for repo in repos_conf:
            repo_abs = os.path.abspath(repo)
            if repo_abs in repos:
                raise RuntimeError('Could not load duplicate repository for path "%s"' % repo_abs)

            repos[repo_abs] = Repo(repo_abs, repos_conf[repo])

        return repos

    def get_repo(self, path):

        for repo in self.repos:
            if self.repos[repo].is_in_repo(path):
                return self.repos[repo]

        raise RuntimeError('Could not find baricadr repository for path "%s"' % path)
