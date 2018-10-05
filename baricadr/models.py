import yaml


class Repo():

    def __init__(self, backend, url, user, password):

        self.backend = backend
        self.url = url
        self.user = user
        self.password = password

    def is_in_repo(self, path):
        return path.startswith(self.url)


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
            # TODO check syntax ok
            # TODO could we get rid of [0] ?
            for repo in repos_conf:
                be = self.backends.get_by_name(repos_conf[repo][0]['backend'])
                self.repos[repo] = Repo(be, repos_conf[repo][0]['url'], repos_conf[repo][0]['user'], repos_conf[repo][0]['password'])

    def get_repo(self, path):

        for x in self.repos:
            if self.repos['x'].is_in_repo(path):
                return self.repos['x']

        raise RuntimeError('Could not find baricadr repository for path "%s"' % path)
