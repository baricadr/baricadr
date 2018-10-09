from subprocess import PIPE, Popen, call


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
    def __init__(self, local_path, url, user, password, exclude):
        self.name = None
        self.url = url
        self.user = user
        self.password = password
        self.exclude = exclude

    def pull(self, path):
        """
        Download a file from remote into local repository

        :type path: str
        :param path: path to pull, without local or remote prefix

        :rtype: ?
        :return: ?
        """
        raise NotImplementedError()


class RcloneBackend(Backend):
    def __init__(self, url, user, password, exclude):
        RcloneBackend.__init__(self, url, user, password, exclude)

    def obscurify_password(self, clear_pass):
        """
        Generate obscure password to connect to distant server
        """
        p = Popen(['rclone', 'obscure', clear_pass], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        retcode = p.returncode
        obscure_password = output.decode('ascii')
        if retcode != 0:
            raise RuntimeError("Child was terminated by signal " + str(retcode) + ": can't obscurify password")

        return obscure_password


class SftpBackend(RcloneBackend):
    def __init__(self, url, user, password, exclude):
        RcloneBackend.__init__(self, url, user, password, exclude)
        self.name = 'sftp'

    def pull(self, path):
        obscure_password = self.obscurify_password(self.password)
        # TODO create temp file for config (https://stackabuse.com/the-python-tempfile-module/) + use --config
        retcode = call('rclone copy ' + SRC_PATH + '/' + path + ' ' + REMOTE + ':' + path + ' --sftp-user ' + user + ' --sftp-pass ' + obscure_password, shell=True)
        if retcode != 0:
            raise RuntimeError("Child was terminated by signal " + str(retcode) + ": can't copy " + SRC_PATH +  '/' +FILE)
            # ERROR_3 : file or dir don't exist


class S3Backend(RcloneBackend):
    def __init__(self, url, user, password, exclude):
        RcloneBackend.__init__(self, url, user, password, exclude)
        self.name = 's3'

    def pull(self):
        print('Here I call rclone ...')
