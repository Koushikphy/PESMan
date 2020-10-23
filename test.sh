set -e

# export/run/import first geom
./PESMan.py export -cid 1 -j 1 -gid 1 -sid 0
cd ExpDir/Export1-multi1/
python RunJob1.py
cd ../..
./PESMan.py import -e ExpDir/Export1-multi1/export.dat -zip   # not deleting the folder


# export/run/import second geom
./PESMan.py export -cid 1 -j 1 -gid 2 -sid 1
cd ExpDir/Export2-multi1/
python RunJob2.py
cd ../..
./PESMan.py import -e ExpDir/Export2-multi1/export.dat -zip


# pass commandline arguments as <process> <includepath> <jobs>
python python RunManager.py 1 0 100  # first 100 jobs serially
python python RunManager.py 4 0 12000 # non path parallel jobs
python python RunManager.py 4 1 12000 # path jobs


