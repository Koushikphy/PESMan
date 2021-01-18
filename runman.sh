#!/bin/bash
# only used when submitting jobs with PBS
#PBS -N rho_6.0
#PBS -j oe
#PBS -l nodes=node1
#cd $PBS_O_WORKDIR 

set -e

# create database and add the calculations
python CreateNewDbs.py 10.0
python PESMan.py addcalc

# run the multi jobs, first one has to be run manually
./PESMan.py export -cid 1 -gid 1 -sid 0
cd ExpDir/Export1-multi1
python RunJob1.py
cd ../../
./PESMan.py import -e ExpDir/Export1-multi1/export.dat -del -zip

# second one doesn't have the first as neighbour, so run this also in manually
python PESMan.py export -cid 1 -gid 2 -sid 1
cd ExpDir/Export2-multi1
python RunJob2.py
cd ../../
./PESMan.py import -e ExpDir/Export2-multi1/export.dat -del -zip

# pass commandline arguments as <calcID> <process> <includepath> <maxJobs> <perIterJob>
python RunManager.py 1 1 0 150 1  # first 100 jobs serially
python RunManager.py 1 4 0 2000 4   # non path parallel jobs 
python RunManager.py 1 4 0 12000 20 # non path parallel jobs in higher bunches
python RunManager.py 1 4 1 12000 20 # path jobs

# run the mrci nact jobs
python RunManager.py 2 4 1 12000 50 

# import energy values from the failed nact jobs
ls ExpDir/Export*-mrciddr2/export.dat | xargs python collectFailed.py
