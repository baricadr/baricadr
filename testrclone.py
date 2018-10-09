# -*- coding: utf-8 -*-

from subprocess  import run, call, PIPE, Popen

SRC_PATH="/tmp"
DEST_PATH="/tmp/"
FILE="dir"
TYPE_TRANSFERT="copy" #move
REMOTE="sftp"
password='test293544'
user='toto'

#generate obscure password for connect to distant server
try:
    p = Popen(['rclone', 'obscure', password], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    retcode = p.returncode
    obscure_password = output.decode('ascii')
    if retcode != 0:
        raise RuntimeError("Child was terminated by signal " + str(retcode)+"can't generate password")
except OSError as e:
    print("Execution failed:"+e, file=sys.stderr)
    sys.exit(1)

#pull data with ftp
try:
    print('rclone '+TYPE_TRANSFERT+' '+SRC_PATH+'/'+FILE+' '+REMOTE+':'+DEST_PATH+' --sftp-user '+ user +' --sftp-pass ' + obscure_password)
    retcode = call('rclone '+TYPE_TRANSFERT+' '+SRC_PATH+'/'+FILE+' '+REMOTE+':'+DEST_PATH+' --sftp-user '+ user +' --sftp-pass ' + obscure_password, shell=True)
    if retcode != 0:
        raise RuntimeError("Child was terminated by signal " + str(retcode)+"can't upload" + SRC_PATH +  '/' +FILE)
        #ERROR_3 : file or dir don't exist
except OSError as e:
    print("Execution failed:"+e, file=sys.stderr)
    sys.exit(1)
