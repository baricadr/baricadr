# -*- coding: utf-8 -*-


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
        #TEST infra Rclone
        #envoi des fichiers
        #
