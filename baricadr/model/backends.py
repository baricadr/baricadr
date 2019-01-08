import json
import os
import tempfile
from subprocess import PIPE, Popen

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
            raise RuntimeError("Child was terminated by signal " + str(retcode) + ": can't obscurify password (stderr: " + str(err) + ")")

        return obscure_password

    def remote_is_single(self, repo, path):
        """
        Check if distant path is a single file or not
        """

        remote_list = self.remote_list(repo, path)
        return len(remote_list) == 1

    # TODO expose remote_list in api ?
    # TODO we could use the --hash option of lsjson (may be slow, but may be useful)
    def remote_list(self, repo, path, full=False):
        """
        List content in a distant path
        """
        obscure_password = self.obscurify_password(self.password)
        tempRcloneConfig = self.temp_rclone_config()

        rel_path = repo.relative_path(path)

        src = "%s:%s%s" % (self.name, self.remote_prefix, rel_path)

        cmd = "rclone lsjson -R --config '%s' '%s' --sftp-user '%s' --sftp-pass '%s'" % (tempRcloneConfig.name, src, self.user, obscure_password)
        current_app.logger.info(cmd)
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        retcode = p.returncode
        try:
            json_output = json.loads(output.decode('ascii'))
        except json.decoder.JSONDecodeError:
            current_app.logger.error('Failed to parse json output from rclone lsjson: %s' % output.decode('ascii'))

        if retcode != 0:
            current_app.logger.error(output)
            current_app.logger.error(err)
            raise RuntimeError("Child was terminated by signal " + str(retcode) + ": can't run rclone lsjon (stderr: " + str(err) + ")")

        current_app.logger.info('Raw output from rclone lsjson: %s' % json_output)

        if full:
            remote_list = json_output
        else:
            remote_list = []
            for entry in json_output:
                if not entry['IsDir']:
                    remote_list.append(entry['Path'])
            tempRcloneConfig.close()

        current_app.logger.info('Parsed remote listing from rclone: %s' % remote_list)

        return remote_list

    def temp_rclone_config(self):
        tempRcloneConfig = tempfile.NamedTemporaryFile('w+t')
        tempRcloneConfig.write('[' + self.name + ']\n')
        tempRcloneConfig.write('type = ' + self.name + '\n')
        tempRcloneConfig.write('host = ' + self.remote_host + '\n')
        tempRcloneConfig.seek(0)

        return tempRcloneConfig


class SftpBackend(RcloneBackend):
    def __init__(self, conf):
        RcloneBackend.__init__(self, conf)
        self.name = 'sftp'

        url_split = self.url.split(":")
        self.remote_host = url_split[0]
        self.remote_prefix = os.path.join(url_split[1], '')

    def pull(self, repo, path):
        obscure_password = self.obscurify_password(self.password)
        tempRcloneConfig = self.temp_rclone_config()

        rclone_cmd = 'copy'
        if self.remote_is_single(repo, path):
            rclone_cmd = 'copyto'

        rel_path = repo.relative_path(path)

        src = "%s:%s%s" % (self.name, self.remote_prefix, rel_path)
        dest = "%s" % (path)

        ex_options = ''
        if repo.exclude:
            excludes = repo.exclude.split(',')
            for ex in excludes:
                ex_options += " --exclude '%s'" % ex.strip()

        # We use --ignore-existing to avoid deleting locally modified files (for example if a file was modified locally but the backup is not yet up-to-date)
        cmd = "rclone %s --ignore-existing --config '%s' '%s' '%s' --sftp-user '%s' --sftp-pass '%s' %s" % (rclone_cmd, tempRcloneConfig.name, src, dest, self.user, obscure_password, ex_options)
        current_app.logger.debug("Running command: %s" % cmd)
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        retcode = p.returncode

        if retcode != 0:
            current_app.logger.error(output)
            current_app.logger.error(err)
            raise RuntimeError("Child was terminated by signal %s: can't copy %s (stderr: " + str(err) + ")" % (retcode, path))
        tempRcloneConfig.close()


class S3Backend(RcloneBackend):
    def __init__(self, conf):
        RcloneBackend.__init__(self, conf)
        self.name = 's3'

    def pull(self, repo, path):
        raise NotImplementedError()
