# -*- coding: utf-8 -*-

class Repo():

    self.backend = None
    self.url = None
    self.user = None
    self.password = None
    ...

    def __init__(backend, ...):
        self.backend = backend # TODO fetch a Backend object

    def is_in_repo(self, path):
        return path.startswith(self.url)

class Config():

    def __init__():
        # TODO open the config file, from the option given to uwsgi
        self.repos = {}

        read_conf("path/to/config.yml")

    def read_conf(self, path):

        self.repos[''] = Repo(backend, url, ...)

    def get_repo(self, path):

        for x in self.repo:
            if self.repo['x'].is_in_repo(path):
                return self.repo['x']
