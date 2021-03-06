import json
import os
import tempfile
import time
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


# TODO [HI] check that we support symlinks now (https://github.com/ncw/rclone/issues/1152)
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

        remote_list = self.remote_list(repo, path, max_depth=0)
        return len(remote_list) == 1

    # TODO [LOW] we could use the --hash option of lsjson (may be slow, but may be useful)
    def remote_list(self, repo, path, missing=False, max_depth=1, from_root=False, full=False):
        """
        List content in a distant path
        """
        obscure_password = self.obscurify_password(self.password)
        tempRcloneConfig = self.temp_rclone_config()

        rel_path = repo.relative_path(path)

        src = "%s:%s%s" % (self.name, self.remote_prefix, rel_path)

        max_depth_command = ""

        try:
            max_depth = int(max_depth)
        except ValueError:
            max_depth = 1
        # If not 0 (0 is for listing all)
        if max_depth:
            max_depth_command = "--max-depth " + str(max_depth)

        cmd = "rclone lsjson -R --config '%s' '%s' --sftp-user '%s' --sftp-pass '%s' %s" % (tempRcloneConfig.name, src, self.user, obscure_password, max_depth_command)
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

        path_rel_prefix = rel_path
        if len(json_output) == 1 and not json_output[0]['IsDir']:
            path_rel_prefix = os.path.dirname(rel_path)

        remote_list = []
        for entry in json_output:
            if not entry['IsDir']:
                if from_root:
                    file_path = os.path.join(path_rel_prefix, entry['Path'])
                else:
                    file_path = entry['Path']

                if full:
                    entry['Path'] = file_path
                    remote_list.append(entry)
                else:
                    remote_list.append({'Path': file_path})

        tempRcloneConfig.close()
        if missing:
            remote_list = self.missing_list(path, remote_list, max_depth, repo, full)

        current_app.logger.info('Parsed remote listing from rclone: %s' % remote_list)

        return remote_list

    def missing_list(self, path, remote_list, max_depth, repo, full=False):

        remote_set = set([value['Path'] for value in remote_list])

        if os.path.isfile(path):
            file_set = set([repo.relative_path(path)])
            return list(remote_list - file_set)

        file_set = set()
        for dir_, _, files in self.restricted_walk(path, max_depth):
            for file_name in files:
                rel_dir = os.path.relpath(dir_, path)
                rel_file = os.path.join(rel_dir, file_name)
                file_set.add(rel_file.lstrip("./"))

        sorted_list = sorted(list(remote_set - file_set))

        if full:
            return [file_dict for file_dict in remote_list if file_dict['Path'] in sorted_list]
        else:
            return [{'Path': file_path} for file_path in sorted_list]

    def restricted_walk(self, path, max_depth):
        dirs, nondirs = [], []
        for entry in os.scandir(path):
            (dirs if entry.is_dir() else nondirs).append(entry.name)
        yield path, dirs, nondirs
        if not max_depth or max_depth > 1:
            for name in dirs:
                for x in self.restricted_walk(os.path.join(path, name), 0 if not max_depth else max_depth - 1):
                    yield x

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
            raise RuntimeError("Child was terminated by signal %s: can't copy %s (stderr: %s)" % (retcode, path, str(err)))
        tempRcloneConfig.close()

        # Touch all files to set atime to now (but not mtime)
        if self.remote_is_single(repo, path):
            os.utime(path, (time.time(), os.stat(path).st_mtime))
        else:
            for root, subdirs, files in os.walk(path):
                for name in files:
                    candidate = os.path.join(root, name)
                    os.utime(candidate, (time.time(), os.stat(candidate).st_mtime))


class S3Backend(RcloneBackend):
    def __init__(self, conf):
        RcloneBackend.__init__(self, conf)
        self.name = 's3'

    def pull(self, repo, path):
        raise NotImplementedError()
