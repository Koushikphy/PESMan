from __future__ import print_function
import paramiko 


def getDetails(userName, ip, location, passwd=None):

    print('='*90)
    print("\033[1mHost : {}\nLocation : {}\n\033[0m".format(userName, location))

    client = paramiko.SSHClient()
    client._policy = paramiko.WarningPolicy()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # ssh_config = paramiko.SSHConfig()
    # user_config_file = os.path.expanduser("~/.ssh/config")
    # if os.path.exists(user_config_file):
    #     with open(user_config_file) as f:
    #         ssh_config.parse(f)

    client.connect(
        ip,
        port='22',
        username=userName,
        password=passwd
    )

    _,b,_ = client.exec_command('cd {}; python PESMan.py status'.format(location))

    for i in b.readlines(): print(i,end='')


    _,b,_ = client.exec_command("""
        python -c "import os;import time ;print(time.ctime(os.path.getmtime(os.path.expanduser('{}/h3.db'))))"
    """.format(location))
    bb = b.readline()
    print("Database last modified on : ",bb)
    print('-'*90,'\n')
    client.close()


getDetails('bijit', '192.168.31.164', "/home/bijit/KOUSHIK/H3_AB_INITIO/RHO_7.25")
getDetails('sandip', '192.168.31.59', "~/KOUSHIK/H3_AB_INITIO/RHO_8.25")