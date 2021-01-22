from __future__ import print_function
import paramiko,os, subprocess,time


def getRemoteDetails(userName, ip, location, passwd=None):


    client = paramiko.SSHClient()
    client._policy = paramiko.WarningPolicy()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


    client.connect(
        ip,
        port='22',
        username=userName,
        password=passwd
    )

    for loc in location:
        print('='*90)
        print("\033[1mHost : {}\nLocation : {}\n\033[0m".format(userName, loc))

        _,b,_ = client.exec_command('cd {}; python PESMan.py status'.format(loc))

        for i in b.readlines(): print(i,end='')


        _,b,_ = client.exec_command("""
            python -c "import os;import time ;print(time.ctime(os.path.getmtime(os.path.expanduser('{}/h3.db'))))"
        """.format(loc))
        bb = b.readline()
        print("Database last modified on : ",bb)
        print('-'*90,'\n')
    client.close()






def getLocalDetails(location):
    currentDir = os.getcwd()
    os.chdir(location)
    subprocess.call('python PESMan.py status', shell=True)
    print(time.ctime(os.path.getmtime('h3.db')))
    os.chdir(currentDir)
