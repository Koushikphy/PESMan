#!/bin/bash

#To exit the script as soon as one of the commands failed
#--------------------------------------------------------
set -e                     
#--------------------------------------------------------

NN=10

I=`sqlite3 no2db.db "SELECT id FROM exports ORDER BY id DESC LIMIT 1" `
N=`echo "$I+$NN" | bc -lq`


while [ "$I" -lt "$N" ]
do

  ./PESMan.py export -j 1 -cid 1 -d 0

  I=`echo "$I+1" | bc -lq`
  CJDir=Export$I-multiana1

  cd ExpDir/$CJDir
  ./RunJob$I.py
  cd -

  python PESMan.py import -e ExpDir/$CJDir/export.dat -del

done
