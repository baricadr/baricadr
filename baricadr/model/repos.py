import os

from baricadr.db_models import PullTask

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

        with open(path, 'r') as stream:
            self.repos = self.do_read_conf(stream.read())

    def read_conf_from_str(self, content):

        self.repos = self.do_read_conf(content)

    def do_read_conf(self, content):

        repos = {}
        repos_conf = yaml.safe_load(content)
        if not repos_conf:
            raise ValueError("Malformed repository definition '%s'" % content)

        for repo in repos_conf:
            # We use realpath instead of abspath to resolve symlinks and be sure the user is not doing strange things
            repo_abs = os.path.realpath(repo)
            if not os.path.exists(repo_abs):
                current_app.logger.warning("Directory '%s' does not exist, creating it" % repo_abs)
                os.makedirs(repo_abs)
            if repo_abs in repos:
                raise ValueError('Could not load duplicate repository for path "%s"' % repo_abs)

            for known in repos:
                if self._is_subdir_of(repo_abs, known):
                    raise ValueError('Could not load repository for path "%s", conflicting with "%s"' % (repo_abs, known))

            repos[repo_abs] = Repo(repo_abs, repos_conf[repo])

        return repos

    def _is_subdir_of(self, path1, path2):

        if path1 == path2:
            return True

        if len(path1) > len(path2):
            if path2 == path1[:len(path2)]:
                return True
        elif len(path1) < len(path2):
            if path1 == path2[:len(path1)]:
                return True

        return False

    def get_repo(self, path):

        for repo in self.repos:
            if self.repos[repo].is_in_repo(path):
                return self.repos[repo]

        raise RuntimeError('Could not find baricadr repository for path "%s"' % path)

    def is_already_pulling(self, path):
        """
        If a task is already pulling path or an upper directory, returns the task id.
        Return False otherwise.
        """

        running_tasks = PullTask.query.all()
        for rt in running_tasks:
            if path.startswith(rt.path):
                return rt.task_id

        return False

    def is_locked_by_subdir(self, path):
        """
        If some tasks are already pulling a subdirectory of path, returns the list of task ids.
        Return an empty list otherwise.
        """

        running_tasks = PullTask.query.all()
        locking = []
        for rt in running_tasks:
            if rt.path.startswith(path) and path != rt.path:
                locking.append(rt.task_id)

        return locking
