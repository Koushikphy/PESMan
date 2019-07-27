#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
from datetime import datetime
from contextlib import contextmanager



@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def writeLog(fLog, msg, cont=False): # writes to the log file
    if not cont : 
        msg = '{:.<90}'.format(datetime.now().strftime("[%d-%m-%Y %I:%M:%S %p]     ") + msg)
    else:
        msg+='\n'
    fLog.write(msg)
    fLog.flush()


def RunExportedCalcs(ScrDirCalc):
    """ Run or continue a series of exported jobs."""

    # first open export.dat file and collect information about exported jobs
    with open("export.dat",'r') as f:
        sExpDat = f.read().split("\n",1)[1]

    # obtain a list of incomplete jobs
    # such jobs will not have corresponding .calc file, but .calc_ file
    CalcDirs = sExpDat.split()
    DirsDone = [d for d in CalcDirs if os.path.isfile(d+"/"+d+".calc")]
    DirsToDo = [d for d in CalcDirs if os.path.isfile(d+"/"+d+".calc_")]

    #    if len(CalcDirs) != len(DirsDone) + len(DirsToDo):
    #       raise Exception("Some dirs in this export directory = " + os.getcwd() + " seem to not have .calc/.calc_ file.")

    # open log file in append mode
    fLog = open("run.log","a")
    if len(DirsDone):
        txt = "Skipping already compelted job Dir \n" + '\n'.join(DirsDone)
        writeLog(fLog, txt, True)

    # now execute each job
    # is it really needed to make a folder for everny new job then delete it.
    # can't we just do the jobs inside the folder
    for RunDir in DirsToDo:
        writeLog(fLog, "Running Job for "+RunDir)

        # ScrDirCalc = os.path.expanduser(MolproScrDir + "/" + "scr-" + RunDir)
        # os.makedirs(ScrDirCalc,0775)
        fComBaseFile = RunDir + ".com"

        with cd(RunDir):
            exitcode = subprocess.call(["molpro", "-d", ScrDirCalc, "-W .", "-n", "2", fComBaseFile])

        if exitcode == 0:
            writeLog(fLog, "Job Successful.", True)
            # rename .calc_ file so that it can be imported
            os.rename( "{0}/{0}.calc_".format(RunDir), "{0}/{0}.calc".format(RunDir))

        else:
            writeLog(fLog, "Job Failed.", True)

        # remove scratch directory
        # subprocess.call(["rm","-rf",ScrDirCalc])
        # shutil.rmtree(ScrDirCalc)

    writeLog(fLog, "All Jobs Completed\n")
    writeLog(fLog, "."*70, True)
    fLog.close()
    
if __name__ == '__main__':

    # give full path please
    MolproScrDir = "/tmp/bijit/Q1-Q3-NO2"
    RunExportedCalcs(MolproScrDir)



