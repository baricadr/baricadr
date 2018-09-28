# -*- coding: utf-8 -*-

from subprocess  import call
from subprocess  import run

SRC_PATH="/root"
DEST_PATH="/root"
FILE="toto.txt"
TYPE_TRANSFERT="copy" #move

try:
    retcode = call('rclone ls sftp:'+SRC_PATH+'/'+FILE, shell=True)
    if retcode != 0:
        raise RuntimeError("Child was terminated by signal " + str(retcode))
        #3 : file or dir don't exist
except OSError as e:
    print("Execution failed:"+e, file=sys.stderr)
    sys.exit(1)

try:
    retcode = call('rclone '+TYPE_TRANSFERT+' sftp:'+SRC_PATH+'/'+FILE+' '+DEST_PATH, shell=True)
    if retcode != 0:
        raise RuntimeError("Child was terminated by signal " + str(retcode))
except OSError as e:
    print("Execution failed:"+e, file=sys.stderr)
    sys.exit(1)


"""if subprocess.check_output(['rclone', 'ls','sftp:'+PATH+'/'+FILE], check=True):
    subprocess.run(['rclone', 'ls','sftp:'+PATH])
else:
    print("error")
#subprocess.run(['rclone','move',PATH+'/'+FILE,'sftp:'+PATH])
#subprocess.run(['rclone', 'ls','sftp:'+PATH+'/'+FILE])"""
