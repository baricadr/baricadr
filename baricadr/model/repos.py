import datetime
import fnmatch
import os
import tempfile
import time

from baricadr.db_models import BaricadrTask
from baricadr.utils import get_celery_tasks

import dateutil.parser

from flask import current_app

from tzlocal import get_localzone

import yaml


class Repo():

    def __init__(self, local_path, conf):

        if 'backend' not in conf:
            raise ValueError("Malformed repository definition, missing backend '%s'" % conf)

        self.local_path = local_path  # No trailing slash

        perms = self._check_perms()
        if not perms['writable']:
            raise ValueError("Path '%s' is not writable" % local_path)

        self.exclude = None
        if 'exclude' in conf:
            self.exclude = conf['exclude']
        self.conf = conf

        # Owner conf
        self.chown_uid = None
        self.chown_gid = None
        if 'chown_uid' in conf:
            try:
                conf['chown_uid'] = int(conf['chown_uid'])
            except ValueError:
                raise ValueError("Malformed repository definition, chown_uid must be a valid linux uid '%s'" % conf)

            if conf['chown_uid'] < 0 or conf['chown_uid'] > 65536:
                raise ValueError("Malformed repository definition, chown_uid must be a valid linux uid '%s'" % conf)

            self.chown_uid = conf['chown_uid']

        if 'chown_gid' in conf:
            try:
                conf['chown_gid'] = int(conf['chown_gid'])
            except ValueError:
                raise ValueError("Malformed repository definition, chown_gid must be a valid linux gid '%s'" % conf)

            if conf['chown_gid'] < 0 or conf['chown_gid'] > 65536:
                raise ValueError("Malformed repository definition, chown_gid must be a valid linux gid '%s'" % conf)

            self.chown_gid = conf['chown_gid']

        # Default behaviour should be non-freeze
        self.freezable = False
        if 'freezable' in conf and conf['freezable'] is True:

            self.disable_atime_test = False
            if 'disable_atime_test' in conf and conf['disable_atime_test'] is True:
                self.disable_atime_test = True

            # Skip if not freezable
            if not perms['freezable']:
                if self.disable_atime_test:
                    current_app.logger.warning("The local path '%s' does not support atime, marking as freezable anyway because disable_atime_test is set." % local_path)
                else:
                    raise ValueError("Malformed repository definition for local path '%s', this path does not support atime" % local_path)

            # If freezable, set freeze_age
            self.freezable = True
            self.freeze_age = 180
            if 'freeze_age' in conf:
                try:
                    conf['freeze_age'] = int(conf['freeze_age'])
                except ValueError:
                    raise ValueError("Malformed repository definition, freeze_age must be an integer in days in '%s'" % conf)

                if conf['freeze_age'] < 2 or conf['freeze_age'] > 10000:
                    raise ValueError("Malformed repository definition, freeze_age must be an integer in days >1 and <10000 in '%s'" % conf)

                self.freeze_age = conf['freeze_age']

            self.auto_freeze = False
            if 'auto_freeze' in conf and conf['auto_freeze'] is True:
                self.auto_freeze = True
                self.auto_freeze_interval = 7
                if 'auto_freeze_interval' in conf:
                    try:
                        conf['auto_freeze_interval'] = int(conf['auto_freeze_interval'])
                    except ValueError:
                        raise ValueError("Malformed repository definition, auto_freeze_interval must be an integer in days in '%s'" % conf)

                    if conf['auto_freeze_interval'] < 2 or conf['auto_freeze_interval'] > 10000:
                        raise ValueError("Malformed repository definition, auto_freeze_interval must be an integer in days >1 and <10000 in '%s'" % conf)

                self.auto_freeze_interval = conf['auto_freeze_interval']
        self.backend = current_app.backends.get_by_name(conf['backend'], conf)

    def is_in_repo(self, path):
        path = os.path.join(path, "")

        return path.startswith(os.path.join(self.local_path, ""))

    def pull(self, path, dry_run=False):
        """
        Pull files from remote repository

        :type path: str
        :param path: Path where baricadr should pull files

        :type dry_run: bool
        :param dry_run: Do not pull anything, just print what would be done in normal mode.
        """
        res = self.backend.pull(self, path, dry_run=dry_run)

        if not dry_run:
            # Touch all pulled files to set atime to now (but not mtime)
            self.touch_atime(path)

            # Set owner of pulled files
            self.set_owner(path)

        return res

    def touch_atime(self, path):
        # Touch all pulled files to set atime to now (but not mtime)
        current_app.logger.info("Setting atime to path '%s'" % path)
        if os.path.isfile(path):
            os.utime(path, (time.time(), os.lstat(path).st_mtime), follow_symlinks=False)
        else:
            for root, subdirs, files in os.walk(path):
                for name in files:
                    candidate = os.path.join(root, name)
                    os.utime(candidate, (time.time(), os.lstat(candidate).st_mtime), follow_symlinks=False)

    def set_owner(self, path):
        if self.chown_uid is not None or self.chown_gid is not None:
            current_app.logger.info("Changing owner of path '%s'" % path)
            if os.path.isfile(path):
                os.chown(path, self.chown_uid if self.chown_uid is not None else -1,
                         self.chown_gid if self.chown_gid is not None else -1, follow_symlinks=False)
            else:
                for root, subdirs, files in os.walk(path):
                    for name in subdirs:
                        candidate = os.path.join(root, name)
                        os.chown(candidate, self.chown_uid if self.chown_uid is not None else -1,
                                 self.chown_gid if self.chown_gid is not None else -1, follow_symlinks=False)
                    for name in files:
                        candidate = os.path.join(root, name)
                        os.chown(candidate, self.chown_uid if self.chown_uid is not None else -1,
                                 self.chown_gid if self.chown_gid is not None else -1, follow_symlinks=False)

    def remote_is_single(self, path):
        return self.backend.remote_path_number(self, path) == 1

    def relative_path(self, path):
        return path[len(self.local_path) + 1:]

    def remote_list(self, path, missing=False, max_depth=1, from_root=False, full=False):
        """
        List files from remote repository

        :type path: str
        :param path: Path where baricadr should list files

        :type missing: bool
        :param missing: Only list files missing from the local path

        :type from_root: bool
        :param from_root: Return full paths from root of the repo (instead of relative to given path)

        :type max_depth: int
        :param max_depth: Restrict to a max depth. Set to 0 for all files.

        :rtype: list
        :return: list of files
        """

        return self.backend.remote_list(self, path, missing, max_depth, from_root, full)

    def remote_tree(self, path, max_depth=1):
        """
        List files from remote repository, with missing files tagged with a '*'

        :type path: str
        :param path: Path where baricadr should list files

        :type max_depth: int
        :param max_depth: Restrict to a max depth. Set to 0 for all files.

        :rtype: list
        :return: list of files
        """

        return self.backend.remote_tree(self, path, max_depth)

    def freeze(self, path, force=False, dry_run=False):
        """
        Remove files from local repository

        :type path: str
        :param path: Path where baricadr should freeze files

        :type force: bool
        :param force: Force freezing path, even if files were accessed recently.

        :type dry_run: bool
        :param dry_run: Do not remove anything, just print what would be done in normal mode.

        :rtype: list
        :return: list of freezed files
        """

        current_app.logger.info("Asked to freeze '%s'" % path)

        if not (force or self.freezable):
            return ([], 0)

        remote_list = self.remote_list(path, max_depth=0, from_root=True, full=True)

        if len(remote_list) == 0:
            # SFTP backend throws a RuntimeError when calling remote_list(), make sure we do the same for other backends
            raise RuntimeError("File/directory not found on remote repository: %s" % (path))

        freezables = self._get_freezable(path, remote_list, force)

        current_app.logger.info("Freezable files: %s" % freezables)

        freezed_size = 0
        for tofreeze in freezables:
            freezed_size += os.path.getsize(tofreeze)

        for to_freeze in freezables:
            if dry_run:
                current_app.logger.info("Would freeze '%s' (dry-run mode)" % (to_freeze))
            else:
                current_app.logger.info("Freezing '%s'" % (to_freeze))
                self._do_freeze(to_freeze)

        return (freezables, freezed_size)

    # Might actually use this to run safety checks (can_write? others?)
    def _check_perms(self):
        if not current_app.is_worker:
            # The web app doesn't need to have write access, nor to check if the repo is freezable
            current_app.logger.debug("Web process, skipping perms checks for repo %s" % (self.local_path))
            return {"writable": True, "freezable": True}

        perms = {"writable": True, "freezable": False}
        try:
            # Sometimes tmp file can escape their deletion: I guess it comes from multiple live code reload in dev mode
            with tempfile.NamedTemporaryFile(dir=self.local_path) as test_file:
                starting_atime = os.stat(test_file.name).st_atime
                # Need to wait a bit
                time.sleep(1)
                test_file.read()
                if not os.stat(test_file.name).st_atime == starting_atime:
                    perms["freezable"] = True
        except OSError as err:
            current_app.logger.error("Got error while checking perms on %s: %s" % (self.local_path, err))
            perms["writable"] = False

        current_app.logger.info("Worker process, perms detected for repo %s: %s" % (self.local_path, perms))

        return perms

    def _get_freezable(self, path, remote_list, force=False):
        freezables = []

        excludes = []
        if self.exclude:
            excludes = self.exclude.split(',')

        if os.path.exists(path) and os.path.isfile(path):
            for ex in excludes:
                if fnmatch.fnmatch(path, ex.strip()):
                    current_app.logger.info("Found excluded path: %s with expression %s" % (path, ex.strip()))
                    return
            if self._can_freeze(path, remote_list, force):
                freezables.append(path)
        else:
            for root, subdirs, files in os.walk(path):
                for name in files:
                    candidate = os.path.join(root, name)
                    current_app.logger.info("Evaluating freezable for path: %s " % (candidate))
                    excluded = False
                    for ex in excludes:
                        if fnmatch.fnmatch(candidate, ex.strip()):
                            current_app.logger.info("Found excluded path: %s with expression %s" % (candidate, ex.strip()))
                            excluded = True
                            break
                    if not excluded and self._can_freeze(candidate, remote_list, force):
                        freezables.append(candidate)

        return freezables

    def _can_freeze(self, file_to_check, remote_list, force):
        """
        Check if a file should be freezed or not

        :type file_to_check: str
        :param file_to_check: Path of a file to check

        :type remote_list: list
        :param remote_list: List of dicts containing informations about remote files (path, mtime)

        :type force: bool
        :param force: Whether to ignore atime

        :rtype: bool
        :return: True if the file should be freezed
        """

        relative_path = self.relative_path(file_to_check)
        # Check if in remote list
        remote_file = next((item for item in remote_list if item["Path"] == relative_path), None)

        if not remote_file:
            return False

        # Check if modified since pulled
        tz = get_localzone()

        last_modif_remote = dateutil.parser.isoparse(remote_file['ModTime'])
        last_modif_local = datetime.datetime.fromtimestamp(os.lstat(file_to_check).st_mtime, tz=tz)

        current_app.logger.info("Checking if we should freeze '%s': local modification on '%s' , remote modification on '%s' => Delta is %s seconds" % (file_to_check, last_modif_local, last_modif_remote, (last_modif_local - last_modif_remote).total_seconds()))

        # Assuming 10s delay? Maybe more? -> Might need to be fine-tuned. Tests shows 0.22s
        if (last_modif_local - last_modif_remote).total_seconds() > 10:
            return False

        # Skip check if force
        if force:
            current_app.logger.info("Checking if we should freeze '%s' => force is set to True, freezing" % (file_to_check))
            return True

        last_access = datetime.datetime.fromtimestamp(os.lstat(file_to_check).st_atime).date()
        now = datetime.date.today()
        delta = now - last_access
        delta = delta.days
        current_app.logger.info("Checking if we should freeze '%s' (freeze_age=%s): last accessed on %s (%s days ago) =>  %s" % (file_to_check, self.freeze_age, last_access, delta, (force or (delta > self.freeze_age))))

        return delta > self.freeze_age

    def _do_freeze(self, file_to_freeze):
        """
        Removes a cold file from local repository

        :type path: str
        :param path: Path of a file to freeze
        """

        os.unlink(file_to_freeze)


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

        path1 = os.path.join(path1, "")
        path2 = os.path.join(path2, "")

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

        path = os.path.join(path, "")

        for repo in self.repos:
            if self.repos[repo].is_in_repo(path):
                return self.repos[repo]

        raise RuntimeError('Could not find baricadr repository for path "%s"' % path)

    def is_already_touching(self, path):
        """
        If a task is already pulling/freezing path or an upper directory, returns the task id.
        Return False otherwise.
        """

        cel_tasks = get_celery_tasks(current_app.celery)

        running_tasks = BaricadrTask.query.all()
        for rt in running_tasks:
            if rt.finished is None and path.startswith(rt.path):
                if rt.task_id in cel_tasks['active_tasks'] \
                   or rt.task_id in cel_tasks['reserved_tasks'] \
                   or rt.task_id in cel_tasks['scheduled_tasks']:

                    # check if locked by a zombie task
                    return rt.task_id

        return False

    def is_locked_by_subdir(self, path):
        """
        If some tasks are already pulling/freezing a subdirectory of path, returns the list of task ids.
        Return an empty list otherwise.
        """

        cel_tasks = get_celery_tasks(current_app.celery)

        running_tasks = BaricadrTask.query.all()
        locking = []
        for rt in running_tasks:
            if rt.finished is None and rt.path.startswith(path) and path != rt.path:
                if rt.task_id in cel_tasks['active_tasks'] \
                   or rt.task_id in cel_tasks['reserved_tasks'] \
                   or rt.task_id in cel_tasks['scheduled_tasks']:

                    # check if locked by a zombie task
                    locking.append(rt.task_id)

        return locking
