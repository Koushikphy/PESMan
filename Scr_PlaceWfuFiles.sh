#!/bin/bash

if [ -f TempfileGID.tmp ]; then

rm TempfileGID.tmp

fi

ResDir=$1

./PlaceWfuFiles.py $ResDir

input="TempfileGID.tmp"

i=0

while IFS='' read -r var || [[ -n "$var" ]]; do

FILE=$ResDir/$var/$var.wfu

touch $FILE

i=`echo "$i+1" | bc -lq`

done < "$input"

rm TempfileGID.tmp
