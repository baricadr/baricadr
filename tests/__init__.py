import os


class BaricadrTestCase():

    def set_old_atime(self, path, age=500 * 3600, recursive=True):
        """
        Make sure that all files in given directory have an old access time
        """
        if recursive:
            for root, subdirs, files in os.walk(path):
                for name in files:
                    candidate = os.path.join(root, name)
                    mod_time = os.stat(candidate).st_mtime
                    old_time = os.stat(candidate).st_atime - age
                    os.utime(candidate, (old_time, mod_time))
        else:
            mod_time = os.stat(candidate).st_mtime
            old_time = os.stat(path).st_atime - age
            os.utime(path, (old_time, mod_time))
