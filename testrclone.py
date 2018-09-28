# -*- coding: utf-8 -*-

from subprocess  import call
from subprocess  import run

PATH="/root"
FILE="toto.txt"
TYPE_TRANSFERT="copy" #move 

try:
    retcode = call('rclone ls sftp:'+PATH+'/'+FILE, shell=True)
    if retcode != 0:
        raise RuntimeError("Child was terminated by signal " + str(retcode))
    else:
        run(['rclone',TYPE_TRANSFERT,'sftp:'+PATH+'/'+FILE,PATH])
except OSError as e:
    print("Execution failed:"+e, file=sys.stderr)
    sys.exit(1)


"""if subprocess.check_output(['rclone', 'ls','sftp:'+PATH+'/'+FILE], check=True):
    subprocess.run(['rclone', 'ls','sftp:'+PATH])
else:
    print("error")
#subprocess.run(['rclone','move',PATH+'/'+FILE,'sftp:'+PATH])
#subprocess.run(['rclone', 'ls','sftp:'+PATH+'/'+FILE])"""
