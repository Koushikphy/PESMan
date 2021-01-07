import re
import os
# import sys
import shutil
import subprocess
from multiprocessing import Pool
from PESMan import  makeLogger, parseConfig
from ReadResults import runManagerUtil as readResult
from ImpExp import ExportJobs, ImportJobs
# from logging.handlers import TimedRotatingFileHandler



####--------------------User specific options----------------------------#######
process           = 1            # values more than 1 will invoke parallel
calcId            = 1            # calculation ID
depth             = 0            # maximum depth to look for
maxJobs           = 10           # total number of jobs to perform
readResultsStep   = 100          # step to read result
constraint        = None         # geom tag constraints
includePath       = False        # include geoms with `path` tags
ignoreFiles       = []           # ignores the file extensions
deleteAfterImport = True         # delete the files after successful import
zipAfterImport    = True         # archive on save on GeomData
stdOut            = False        # print on terminal
importOnConverge  = True         # only import MCSCF converged results
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------


templ    = None
gidList  = []
sidList  = []
iterFile = 'IterMultiJobs.dat' # saves the MCSCF iterations



#NOTES:
#=======================================================================
# 1. The serial/parallel execution of the job is determined from the `process` value. If its is more than 1 then this
#    script runs the molpro jobs in parallel.
# 2. For simplicity and consistency only the molpro run part is done in parallel, all export/import are done serially,
#    this will cost just few minutes in total run of all multi jobs, so this is not worth complicating things.
# 3. In case of parallel execution, this script is implemented to export <=`process` number of jobs in every iteration.
#    Why? As its using `process`  number of parallel processes, then exporting exactly that many jobs, efficiently uses all
#    the processes and still keeps all  the exports in a small neighbourhood. If a very large number of jobs is exported
#    then some jobs may be exported from a far away  neighbour, which is not expected from this script.
# 4. This exports `process` number of jobs in each iteration and still keeps the total jobs exactly at given `maxJobs`.
#    i.e. If 50 jobs is to be exectuted in 4 process, then in each iteration 4 jobs will be exported except the last where
#    it will export only 2 jobs, making a total of exactly 50 jobs
# 5. When using parallel implementation of the script, its advisable to run the molpro itself in a sinlgle process,
#    so the script uses 1 core to run the molpro whenever the parallel execution is opted. Modify the code below to remove that.
# 6. When running the parallel version DON'T try to stop this with SIGINT ( Ctrl+C shortcut). To kill the job use `kill` utility
#    or SIGSTOP (Ctrl+\)/SIGQUIT (Ctrl+Z)/SIGHUP signals what ever applicable.

# process = int(sys.argv[1])
# includePath = bool(int(sys.argv[2]))
# maxJobs = int(sys.argv[3])


config = parseConfig()

dB      = config['DataBase']['db']
pesDir  = config['Directories']['pesdir']
expDir  = config['Directories']['expdir']
runDir  = config['Directories']['rundir']
impDir  = config['Directories']['impdir']
logFile = config['Log']['logfile']
molInfo = config['molInfo']


isParallel= process >1  # use parallel implementation
if isParallel: molInfo['proc'] = '1'


# create rundir and impdir if does'nt exist
# for fold in [runDir, impDir]:
for fold in [runDir]:
    if not os.path.exists(fold):
        os.makedirs(fold)



#open logfiles
logger = makeLogger(logFile=logFile,stdout=stdOut)
if not os.path.exists(iterFile):
    iterLog= open(iterFile, 'w', buffering=1)
    iterLog.write('GeomId    Iteration No.\n')
else:
    iterLog= open(iterFile, 'a', buffering=1)


logger.info('----------------------------------------------------------')
logger.debug('''Starting PESMan RunManager
----------------------------------------------------------
        Host               :   {}
        Process ID         :   {}
        Total Jobs         :   {}{}
        CalcId             :   {}
        Depth              :   {}
        Result Step        :   {}
        Constraint         :   {}
        Include path       :   {}{}
        Archive            :   {}
        Delete on Import   :   {}
----------------------------------------------------------
'''.format(
    os.uname()[1],os.getpid(), maxJobs,
    "\n        Parallel processes :   {}".format(process) if process>1 else '',
    calcId, depth, readResultsStep, constraint, includePath,
    "\n        Ignore Files       :   {}".format(ignoreFiles) if ignoreFiles else '',
    deleteAfterImport, zipAfterImport
    )
)


def parseIteration(baseName):
    # If this returns `True` then the job is properly successful
    outFile = baseName + '.out'
    gId = re.findall(r'geom(\d+)-', outFile)[0]   # parse goem id, just for note
    try:
        with open(outFile) as f: txt = f.read()
        val = re.findall(r'\s*(\d+).*\n\n\s*\*\* WVFN \*\*\*\*', txt)[0]   # parse the iteration number
        val = int(val)
    except:
        import traceback
        logger.info('Failed to parse MCSCF iteration. %s'%traceback.format_exc())
        return
    iterLog.write('{:>6}     {:>6}\n'.format( gId, val))   # exportId is taken from global
    if importOnConverge and val>38:   # flag true with no convergence, skip
        logger.info('Number of MCSCF iteration for {}: {} Skipping import.'.format(baseName,val))
        return False
    logger.info('Number of MCSCF iteration for {}: {}'.format(baseName,val))
    return True




def utilityFunc(arg): # getting one single individual job directory, inside the rundir
    thisRunDir,baseName = arg
    os.chdir(thisRunDir+'/'+baseName)

    logger.info("Running Molpro Job {} ...".format(baseName))

    exitcode = subprocess.call(
            [molInfo['exe'], "-d", molInfo['scrdir'], "-W .", "-n", molInfo['proc'], baseName+'.com']+ molInfo['extra']
        )

    if exitcode==0:
        logger.info("\nJob Successful for {}".format(baseName))
        #NOTE: if the job crossed maximum iteration then the calc_ file wont be renamed i.e. it would be marked as failed
        if parseIteration(baseName):
            file = "{}.calc".format(baseName)
            os.rename( file+'_', file)    # rename .calc_ file so that it can be imported
            # delete the corresponding export job directory if its successful
    else:
        logger.info("\nJob Failed {} \n\n".format(baseName))

    os.chdir(mainDirectory)
    return exitcode==0   # let the main loop know this job is successful



if __name__ == "__main__":
    jobCounter = 0 # keeps a counter for the done jobs
    mainDirectory = os.getcwd()
    if isParallel: pool = Pool(processes=process)

    try:
        while True:
            if isParallel:
                # check if `process` number of jobs can be exported, keepign total jobs exactly `maxjobs`
                thisJobs = process if maxJobs-jobCounter>process else maxJobs-jobCounter
                logger.debug('  Starting Job No : {}-{}\n{}'.format( jobCounter+1,jobCounter+thisJobs, '*'*75))
            else:
                thisJobs = 1 # not parallel means always export just one job
                logger.debug('  Starting Job No : {}\n{}'.format( jobCounter+1, '*'*75))


            # will be exporting `process` number of jobs to run them in parallel
            thisExpDir, exportId, jobDirs = ExportJobs(dB, calcId, thisJobs, 1, expDir,pesDir, templ, gidList, sidList, depth,
                                                                constraint, includePath, molInfo, False, logger)

            jobCounter += len(jobDirs)  # kept if exactly `process` number of jobs not exported
            thisRunDir  = thisExpDir.replace(expDir, runDir)
            thisImpDir  = thisExpDir.replace(expDir, impDir)

            logger.info("Moving Files to RunDir...\n")
            shutil.copytree(thisExpDir, thisRunDir)


            # only the molpro run will be done in parallel
            if isParallel:
                jobStatus = pool.map(utilityFunc, [[thisRunDir,i] for i in jobDirs])
            else:
                jobStatus = [ utilityFunc([thisRunDir,i]) for i in jobDirs]
            # `thisRunDir` though being a global variable, can't be accessed from `utilityFunc` while on parallel processes,
            # as it is created/updated after the porcess intialization


            # NOTE: Not moving files to impdir, files will be imported directly from rundir, toggle comment to change
            # shutil.move(thisRunDir, impDir)
            thisImpDir = thisRunDir

            logger.info('')

            expFile = thisImpDir+'/export.dat'
            ImportJobs(dB, 1, expFile, pesDir, ignoreFiles, deleteAfterImport, zipAfterImport, logger)

            # now delete the jobs directory in the ExpDir, if they are successful.
            # job directories in RunDir are deleted inside the import funciton
            if all(jobStatus): # all jobs are successful, so delete the whole directory
                shutil.rmtree(thisExpDir)
            else: # some jobs failed so delete the successful ones only
                for stat, fol in zip(jobStatus, jobDirs):
                    if stat: shutil.rmtree(thisExpDir+'/'+fol)

            logger.info('')

            if not jobCounter%readResultsStep:
                logger.info("Reading results from database.")
                readResult(dB)

            if jobCounter >= maxJobs : break


        logger.info("Reading results from database...")
        readResult(dB)
        logger.info("Total number of successful jobs done : {}\n{}\n".format(jobCounter, '*'*75))
    except AssertionError as e:
        logger.info('PESMan RunManager Stopped. %s'%e)
    except:
        logger.exception('PESMan RunManager failed')