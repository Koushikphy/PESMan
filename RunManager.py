import re
import os
import sys
import shutil
import logging
import subprocess
from datetime import datetime
from ConfigParser import SafeConfigParser
from ImpExp import ImportNearNbrJobs, ExportNearNbrJobs
from ReadResults import main as readResult
# from logging.handlers import TimedRotatingFileHandler


####----------User specific options-----------#######

calcId            = 1            # calculation ID
depth             = 0            # maximum depth to look for
maxJobs           = 2            # total number of jobs to perform
readResultsStep   = 25           # step to read result
constraint        = None         # geom tag constraints
includePath       = False        # include geoms with `path` tags
ignoreFiles       = []           # ignores the file extensions
deleteAfterImport = True         # delete the files after successful import
zipAfterImport    = True         # archive on save on GeomData
stdOut            = False        # print on terminal
importOnConverge  = True         # only import MCSCF converged results
#-----------------------------------------------------

templ    = None
gidList  = []
sidList  = []
iterFile = 'IterMultiJobs.dat' # saves the MCSCF iterations
jobs     = 1  # one job in each iteration
#############################################







class MyFormatter(logging.Formatter):
    # a custom formatter to handle different format for different level
    def __init__(self, fmt=None, datefmt="%I:%M:%S %p %d-%m-%Y"):
        logging.Formatter.__init__(self, fmt, datefmt)

    def format(self, record):
        if record.levelno == logging.INFO: self._fmt = "%(message)s"
        elif record.levelno == logging.DEBUG: self._fmt = "[%(asctime)s] - %(message)s"
        result = logging.Formatter.format(self, record)
        return result



# checks for iteration number for import to start
def parseIteration(thisImpDir, eId, expEdDir):
    outFile ='{0}/{1}/{1}.out'.format(thisImpDir, expEdDir)
    gId = re.findall('geom(\d+)-', expEdDir)[0]   # parse goem id, just for note
    try:
        with open(outFile) as f: txt = f.read()
        val = re.findall('\s*(\d+).*\n\n\s*\*\* WVFN \*\*\*\*', txt)[0]   # parse the iteration number
        val = int(val)
    except:
        import traceback
        logger.info('Failed to parse MCSCF iteration. %s'%traceback.format_exc())
        return
    iterLog.write('{:>6}      {:>6}     {:>6}\n'.format(eId, gId, val))
    if importOnConverge and val>38:   # flag true with no convergence, skip
        logger.info('Number of MCSCF iteration: {} Skipping import.\n'.format(val))
        return True
    logger.info('Number of MCSCF iteration: {}\n'.format(val))




def makeLogger(logFile, stdout=False):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = MyFormatter()
    fh = logging.FileHandler(logFile)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # fht = TimedRotatingFileHandler(logFile, when="midnight",backupCount=5)
    # logger.addHandler(fht)
    if stdout:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger





scf= SafeConfigParser()
scf.read('pesman.config')

dB      = scf.get('DataBase', 'db')
pesDir  = scf.get('Directories', 'pesdir')
expDir  = scf.get('Directories', 'expdir')
runDir  = scf.get('Directories', 'rundir')
impDir  = scf.get('Directories', 'impdir')
logFile = scf.get('Log', 'LogFile')
molInfo = dict(scf.items('molInfo'))
try:
    molInfo['extra'] = molInfo['extra'].split(',')
except KeyError:
    molInfo['extra'] = []

# create rundir and impdir if does'nt exist
for fold in [runDir, impDir]:
    if not os.path.exists(fold):
        os.makedirs(fold)



#open logfiles
logger = makeLogger(logFile=logFile,stdout=stdOut)
if not os.path.exists(iterFile):
    iterLog= open(iterFile, 'w', buffering=1)
    iterLog.write('Export Id    GeomId    Iteration No.\n')
else:
    iterLog= open(iterFile, 'a', buffering=1)


logger.info('----------------------------------------------------------')
logger.debug('''Starting PESMan RunManager
----------------------------------------------------------
        Process ID         :   {}
        Total Jobs         :   {}
        CalcId             :   {}
        Depth              :   {}
        Result Step        :   {}
        Constraint         :   {}
        Include path       :   {}
        Ignore Files       :   {}
        Archive            :   {}
        Delete on Import   :   {}
----------------------------------------------------------
'''.format(os.getpid(), maxJobs, calcId, depth, readResultsStep, constraint, includePath, ignoreFiles, deleteAfterImport, zipAfterImport))


# keeps a counter for the done jobs
counter = 0
mainDirectory = os.getcwd()
try:
    for jobNo in range(1,maxJobs+1):
        logger.debug('  Starting Job No : {}\n{}'.format( jobNo, '*'*75))
        thisExpDir, exportId, expEdDir = ExportNearNbrJobs(dB, calcId, jobs, expDir,pesDir, templ, gidList, sidList, depth,
                                                            constraint, includePath, molInfo,logger)
        # folder that contains the com file, should have exported only one job, if not rewrite inner loop
        expEdDir = expEdDir[0]

        thisRunDir = thisExpDir.replace(expDir, runDir)
        thisImpDir = thisExpDir.replace(expDir, impDir)

        logger.info("Moving Files to RunDir...")
        shutil.copytree(thisExpDir, thisRunDir)

        # section that runs the molpro. !NOTE: the `RunJob.py` file created in ImpExp is not used by runmanager
        logger.info("Running Molpro Job...")

        os.chdir(thisRunDir+'/'+expEdDir)    # go inside the exported forlder where the `.com` file is
        exitcode = subprocess.call(["molpro", "-d", molInfo['scrdir'], "-W .", "-n", molInfo['proc'], expEdDir+'.com'] + molInfo['extra'])
        os.chdir(mainDirectory)              # go back to main directory

        if exitcode==0:
            logger.info("Job Successful.")
            file = "{0}/{1}/{1}.calc_".format(thisRunDir, expEdDir)
            os.rename( file+'_', file)    # rename .calc_ file so that it can be imported
        else:
            logger.info("Job Failed.\n\n")
            continue

        # shutil.move(thisRunDir, impDir)
        # NOTE: Not moving files to impdir, files will be imported directly from rundir, toggle comment to change
        thisImpDir = thisRunDir

        # checks and saves MCSCF iteration in `iterLog`
        # blocks the import if `importOnConverge` is ON
        if parseIteration(thisImpDir, exportId, expEdDir): continue
        expFile = thisImpDir+'/export.dat'
        ImportNearNbrJobs(dB, expFile, pesDir, ignoreFiles, deleteAfterImport, zipAfterImport, logger)
        shutil.rmtree(thisExpDir)
        counter+=1
        if not counter%readResultsStep:
            logger.info("Reading results from database.")
            readResult()

    logger.info("Reading results from database...")
    readResult()
    logger.info("Total number of successful jobs done : {}\n{}\n".format(counter, '*'*75))
except AssertionError as e:
    logger.info('PESMan RunManager Stopped. %s'%e)
except:
    logger.exception('PESMan RunManager failed')