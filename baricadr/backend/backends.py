class Backends():
    def __init__(self):
        self.backends = {
            'sftp': SftpBackend,
            's3': SftpBackend,
        }

    def get_by_name(self, name):

        if name in self.backends:
            return self.backends[name]

        raise RuntimeError('Could not find backend named "%s"' % name)


class Backend():
    def __init__(self, url, user, password, exclude):
        self.name = None
        self.url = url
        self.user = user
        self.password = password
        self.exclude = exclude

    def pull():
        raise NotImplementedError()


class RcloneBackend():
    def __init__(self, url, user, password, exclude):
        RcloneBackend.__init__(self, url, user, password, exclude)


class SftpBackend():
    def __init__(self, url, user, password, exclude):
        RcloneBackend.__init__(self, url, user, password, exclude)
        self.name = 'sftp'

    def pull():
        print('Here I call rclone ...')


class S3Backend():
    def __init__(self, url, user, password, exclude):
        RcloneBackend.__init__(self, url, user, password, exclude)
        self.name = 's3'

    def pull():
        print('Here I call rclone ...')
