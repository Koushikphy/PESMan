#!/bin/bash

# Delete the "tmp" file if already exists
if [ -f TempfileGID.tmp ]; then

rm TempfileGID.tmp

fi

calcid=1     

# Obtain the geoms ids that have to be removed
python ListGeomIdsRemove.py

read -p "Do you want to delete the calcs with calcid="$calcid" (y/n): " yn

case $yn in

  [Yy]* ) 

  # Delete the database entries in calc table of the obtained Geom IDs. 
  ./DeleteEntry.py $calcid

  PESDir='GeomData'

  input="TempfileGID.tmp"

  while IFS='' read -r var || [[ -n "$var" ]]; do

  rm -r $PESDir/geom$var/
  #echo "$var deleted!"  

  done < "$input"

  cat TempfileGID.tmp >> RemovedCalcGIDs.dat

  rm TempfileGID.tmp

  echo "List of calcs deleted. The database and PesDir modified.";;

  [Nn]* ) 

  exit;;  

  *) echo "Please answer in 'y' or 'n'.";;

esac

