from ConfigParser import SafeConfigParser
from ImpExp import ImportNearNbrJobs, ExportNearNbrJobs
import os,shutil




def parseIteration(file,gId, eId):
    try:
        with open(file) as f:
            txt = f.read()
        val = re.findall('\s*(\d+).*\n\n\s*\*\* WVFN \*\*\*\*', txt)[0]
        val = int(val)
        if val>38:      # if more than 38 then this true will tell the main function to ignore
            return True
        with open('IterMultiJobs.dat', 'a') as f:
            f.write('GeomI Id {} with Export ID {} has {} iterations.\n'.format(gId, eId, val))
    except Exception as e:
        print( "Can't parse multi iteration number. {}: {}".format(type(e).__name__, e))




scf= SafeConfigParser()
scf.read('pesman.config')


dB = scf.get('DataBase', 'db')
pesDir = scf.get('Directories', 'GeomData')
expDir = scf.get('Directories', 'ExpDir')
runDir = scf.get('Directories', 'RunDir')
impDir = scf.get('Directories', 'ImpDir')


for fold in [runDir, impDir]:
    if not os.path.exists(fold):
        os.makedirs(fold)


# provide user specific options
calcId = 1
jobs = 1
depth = 0
constraint = None
includePath = False
ignoreFiles = []
deleteAfterImport = False
zipAfterImport=False

templ = None
gidList = []
sidList = []


mainDirectory = os.getcwd()


thisExpDir, exportId = ExportNearNbrJobs(dB, calcId, jobs, expDir,pesDir, templ, gidList, sidList, depth, constraint, includePath)
thisRunDir = thisExpDir.replace(expDir, runDir)
thisImpDir = thisExpDir.replace(expDir, ImpDir)
shutil.copytree(thisExpDir, thisRunDir)

os.chdir(thisRunDir)  # go back to main directory
runJobPy = 'RunJob%s.py'%exportId
execfile(runJobPy)

os.chdir(mainDirectory)

shutil.copytree(thisRunDir, thisImpDir)

expFile = thisImpDir+'/export.dat'
ImportNearNbrJobs(dB, expFile, pesDir, ignoreFiles, deleteAfterImport, zipAfterImport)

