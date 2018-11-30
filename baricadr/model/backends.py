import os
import tempfile
from subprocess import PIPE, Popen, call

from flask import current_app


class Backends():
    def __init__(self):
        self.backends = {
            'sftp': SftpBackend,
            's3': S3Backend,
        }

    def get_by_name(self, name, conf):

        if name in self.backends:
            return self.backends[name](conf)

        raise RuntimeError('Could not find backend named "%s"' % name)


class Backend():
    def __init__(self, conf):

        self.name = None

        if 'url' not in conf:
            raise ValueError("Missing 'url' in backend config '%s'" % conf)

        if 'user' not in conf:
            raise ValueError("Missing 'user' in backend config '%s'" % conf)

        if 'password' not in conf:
            raise ValueError("Missing 'password' in backend config '%s'" % conf)

        self.url = conf['url']
        self.user = conf['user']
        self.password = conf['password']

    def pull(self, repo, path):
        """
        Download a file from remote into local repository

        :type repo: Repo object
        :param repo: a Repo object

        :type path: str
        :param path: path to pull, without local or remote prefix

        :rtype: ?
        :return: ?
        """
        raise NotImplementedError()


class RcloneBackend(Backend):
    def __init__(self, conf):
        Backend.__init__(self, conf)

    def obscurify_password(self, clear_pass):
        """
        Generate obscure password to connect to distant server
        """
        cmd = "rclone obscure '%s'" % clear_pass
        current_app.logger.info(cmd)
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        retcode = p.returncode
        obscure_password = output.decode('ascii').strip('\n')
        if retcode != 0:
            current_app.logger.error(output)
            current_app.logger.error(err)
            raise RuntimeError("Child was terminated by signal " + str(retcode) + ": can't obscurify password")

        return obscure_password


class SftpBackend(RcloneBackend):
    def __init__(self, conf):
        RcloneBackend.__init__(self, conf)
        self.name = 'sftp'

        url_split = self.url.split(":")
        self.remote_host = url_split[0]
        self.remote_prefix = os.path.join(url_split[1], '')

    def pull(self, repo, path):
        obscure_password = self.obscurify_password(self.password)
        tempRcloneConfig = tempfile.NamedTemporaryFile('w+t')
        tempRcloneConfig.write('[' + self.name + ']\n')
        tempRcloneConfig.write('type = ' + self.name + '\n')
        tempRcloneConfig.write('host = ' + self.remote_host + '\n')
        tempRcloneConfig.seek(0)

        rel_path = repo.relative_path(path)

        src = "%s:%s%s" % (self.name, self.remote_prefix, rel_path)
        dest = "%s" % (path)

        ex_options = ''
        if repo.exclude:
            excludes = repo.exclude.split(',')
            for ex in excludes:
                ex_options += " --exclude '%s'" % ex.strip()

        # We use --ignore-existing to avoid deleting locally modified files (for example if a file was modified locally but the backup is not yet up-to-date)
        cmd = "rclone copy --ignore-existing --config '%s' '%s' '%s' --sftp-user '%s' --sftp-pass '%s' %s" % (tempRcloneConfig.name, src, dest, self.user, obscure_password, ex_options)
        current_app.logger.debug("Running command: %s" % cmd)
        retcode = call(cmd, shell=True)
        if retcode != 0:
            raise RuntimeError("Child was terminated by signal %s: can't copy %s" % (retcode, path))
            # ERROR_3: file or dir don't exist
        tempRcloneConfig.close()


class S3Backend(RcloneBackend):
    def __init__(self, conf):
        RcloneBackend.__init__(self, conf)
        self.name = 's3'

    def pull(self, repo, path):
        raise NotImplementedError()
