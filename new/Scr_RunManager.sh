#!/bin/bash
#To exit the script as soon as one of the commands failed
#--------------------------------------------------------
set -e                     
#--------------------------------------------------------
# get value from commandline or define it here
if [ -z "$1" ]
  then
    NN=10
  else
    NN=$1
fi

I=`sqlite3 no2db.db "SELECT id FROM exports ORDER BY id DESC LIMIT 1" `
# N=`echo "$I+$NN" | bc -lq`
N=$((I+NN))


while [ "$I" -lt "$N" ]
do

  ./PESMan.py export -j 1 -cid 1 -d 0

  I=$((I+1))
  CJDir=Export$I-multi1

  cd ExpDir/$CJDir
  ./RunJob$I.py
  cd ~-

  python PESMan.py import -e ExpDir/$CJDir/export.dat -del -ig .xml .pun

done
