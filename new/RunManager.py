from ConfigParser import SafeConfigParser
from ImpExp import ImportNearNbrJobs, ExportNearNbrJobs
import os,shutil,re,glob
from datetime import datetime
import ReadResultsMulti as rs


#################################################
# provide user specific options
calcId = 1
depth = 0
maxJobs = 100
raedResultsStep=25
constraint = None
includePath = False
ignoreFiles = []
deleteAfterImport = False
zipAfterImport=False

templ = None
gidList = []
sidList = []
jobs = 1
#############################################



def parseIteration(thisImpDir, eId, expEdDir):
    outFile ='{0}/{1}/{1}.out'.format(thisImpDir, expEdDir)
    gId = re.findall('geom(\d+)-', expEdDir)[0]
    with open(file) as f:
        txt = f.read()
    val = re.findall('\s*(\d+).*\n\n\s*\*\* WVFN \*\*\*\*', txt)[0]
    val = int(val)
    with open('IterMultiJobs.dat', 'a') as f:
        f.write('GeomI Id {} with Export ID {} has {} iterations.\n'.format(gId, eId, val))
    if val>38:      # if more than 38 then this true will tell the main function to ignore
        return True



scf= SafeConfigParser()
scf.read('pesman.config')


dB = scf.get('DataBase', 'db')
pesDir = scf.get('Directories', 'geomdata')
expDir = scf.get('Directories', 'expdir')
runDir = scf.get('Directories', 'rundir')
impDir = scf.get('Directories', 'impdir')
molInfo = scf.items('molInfo')
try:
    molInfo['extra'] = molInfo['extra'].split()
except KeyError:
    molInfo['extra'] = []

# create rundir and impdir if does'nt exist
for fold in [runDir, impDir]:
    if not os.path.exists(fold):
        os.makedirs(fold)

mainDirectory = os.getcwd()

counter = 0

for jobNo in range(1,maxJobs+1):
    print "{}\tStarting Job No : {}{}".format(datetime.now().strftime("[%d-%m-%Y %I:%M:%S %p]"), jobNo, '*'*25)
    thisExpDir, exportId, expEdDir = ExportNearNbrJobs(dB, calcId, jobs, expDir,pesDir, templ, gidList, sidList, depth, constraint, includePath, molInfo)
    expEdDir = expEdDir[0]  # only one job is exported in each run
    thisRunDir = thisExpDir.replace(expDir, runDir)
    thisImpDir = thisExpDir.replace(expDir, ImpDir)

    shutil.copytree(thisExpDir, thisRunDir)

    os.chdir(thisRunDir)  # go back to main directory
    runJobPy = 'RunJob%s.py'%exportId
    execfile(runJobPy)

    os.chdir(mainDirectory)

    shutil.move(thisRunDir, ImpDir)


    if parseIteration(thisImpDir, exportId, expEdDir):
        expFile = thisImpDir+'/export.dat'
        ImportNearNbrJobs(dB, expFile, pesDir, ignoreFiles, deleteAfterImport, zipAfterImport)
        shutil.rmtree(thisExp)
    else:
        print 'Job has more than 38 iteration. Skipping import'
        continue

    counter+=1
    if not counter%raedResultsStep:
        rs.main(dB)

rs.main(dB)
print "Total number of successful jobs done : {}".format(counter)