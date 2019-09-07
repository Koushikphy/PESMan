#!/bin/bash

#To exit the script as soon as one of the commands failed
#--------------------------------------------------------
set -e                     
#--------------------------------------------------------

# Delete the "tmp" file if already exists
if [ -f TempfileGID.tmp ]; then

rm -f TempfileGID.tmp

fi

calcid=1     

# Obtain the geoms ids that have to be removed
python ListGeomIdsRemove.py

read -p "Do you want to delete the calcs with calcid="$calcid" (y/n): " yn

case $yn in

  [Yy]* ) 

  # Delete the database entries in calc table of the obtained Geom IDs. 
  ./DeleteEntry.py $calcid

  extcd=$?

  if [ "$extcd" -ne 0 ]
  then

    echo "Error in executing DeleteEntry.py! Check carefully!!!"

    exit 1

  fi

  PESDir='GeomData'

  input="TempfileGID.tmp"

  cnt=0

  while IFS='' read -r var || [[ -n "$var" ]]; do

  rm -rf $PESDir/geom$var/

  cnt=$(( cnt + 1 ))

  done < "$input"

  cat TempfileGID.tmp >> RemovedCalcGIDs.dat

  rm -f TempfileGID.tmp

  echo "$cnt no. of calcs deleted. The database and PesDir modified.";;

  [Nn]* ) 

  exit;;  

  *) echo "Please answer in 'y' or 'n'.";;

esac

