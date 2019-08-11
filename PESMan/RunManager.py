import re 
import os
import shutil
from datetime import datetime
from ConfigParser import SafeConfigParser
from ImpExp import ImportNearNbrJobs, ExportNearNbrJobs
from ReadResultsMulti import main as readResult


#################################################
# provide user specific options
calcId = 1
depth = 0
maxJobs = 5
raedResultsStep=25
constraint = None
includePath = False
ignoreFiles = []
deleteAfterImport = True
zipAfterImport=True

templ = None
gidList = []
sidList = []
jobs = 1
#############################################

print('''
--------------------------------------------------
        Starting PESMan RunManager
--------------------------------------------------
Total Jobs         :   {}
CalcId             :   {}
Depth              :   {}
Result Step        :   {}
Constraint         :   {}
Include path       :   {}
Ignore Files       :   {}
Archive            :   {}
Delete on Import   :   {}
--------------------------------------------------
'''.format(maxJobs, calcId, depth, raedResultsStep, constraint, includePath, ignoreFiles, deleteAfterImport, zipAfterImport))




# cheks for calc file first and then checks for iteration number for import to start
# import will occur only if this function returns true
def parseIteration(thisImpDir, eId, expEdDir):
    outFile ='{0}/{1}/{1}.out'.format(thisImpDir, expEdDir)
    calcExists =  os.path.exists(outFile.replace('out','calc'))
    if not calcExists:
        print('No calc file found. Job may have failed. Skipping Import...')
        return
    gId = re.findall('geom(\d+)-', expEdDir)[0]   # parse goem id, just for note
    with open(outFile) as f:
        txt = f.read()
    val = re.findall('\s*(\d+).*\n\n\s*\*\* WVFN \*\*\*\*', txt)[0]   # parse the iteration number
    with open('IterMultiJobs.dat', 'a') as f:
        f.write('{:>6}      {:>6}     {:>6}\n'.format(eId, gId, val))
    if int(val)<38:
        return True
    else:
        print('Job has more than 38 iteration. Skipping import...')



scf= SafeConfigParser()
scf.read('pesman.config')


dB = scf.get('DataBase', 'db')
pesDir = scf.get('Directories', 'pesdir')
expDir = scf.get('Directories', 'expdir')
runDir = scf.get('Directories', 'rundir')
impDir = scf.get('Directories', 'impdir')
molInfo = dict(scf.items('molInfo'))
try:
    molInfo['extra'] = molInfo['extra'].split(',')
except KeyError:
    molInfo['extra'] = []

# create rundir and impdir if does'nt exist
for fold in [runDir, impDir]:
    if not os.path.exists(fold):
        os.makedirs(fold)

mainDirectory = os.getcwd()

with open('IterMultiJobs.dat', 'a') as f:
    f.write('Export Id    GeomId    Iteration No.\n')

# keeps a counter for the done jobs
counter = 0

for jobNo in range(1,maxJobs+1):
    print("\n\n{}\tStarting Job No : {}\n{}".format(datetime.now().strftime("[%d-%m-%Y %I:%M:%S %p]"), jobNo, '*'*75))
    thisExpDir, exportId, expEdDir = ExportNearNbrJobs(dB, calcId, jobs, expDir,pesDir, templ, gidList, sidList, depth,
                                                         constraint, includePath, molInfo)

    thisRunDir = thisExpDir.replace(expDir, runDir)
    thisImpDir = thisExpDir.replace(expDir, impDir)

    print("\nMoving Files to RunDir...")
    shutil.copytree(thisExpDir, thisRunDir)

    os.chdir(thisRunDir)  
    runJobPy = 'RunJob%s.py'%exportId
    print("Running Molpro Job...")
    execfile(runJobPy)

    os.chdir(mainDirectory) # go back to main directory

    shutil.move(thisRunDir, impDir)

    # only one job is exported in each run in this case
    # if multiple job is exported then have to check for each directory
    expEdDir = expEdDir[0]  
    if parseIteration(thisImpDir, exportId, expEdDir):
        expFile = thisImpDir+'/export.dat'
        ImportNearNbrJobs(dB, expFile, pesDir, ignoreFiles, deleteAfterImport, zipAfterImport)
        shutil.rmtree(thisExpDir)
        counter+=1
        if not counter%raedResultsStep:
            print("Reading results from database...")
            readResult(dB)

print("\nReading results from database...",)
readResult(dB)
print("done.")
print("\nTotal number of successful jobs done : {}\n{}".format(counter, '*'*75))
