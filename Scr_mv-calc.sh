#!/bin/bash

if [ -f TempfileGID.tmp ]; then

rm TempfileGID.tmp

fi

ResDir=$1

./PlaceWfuFiles.py $ResDir

input="TempfileGID.tmp"

i=0

while IFS='' read -r var || [[ -n "$var" ]]; do

CALC=$ResDir/$var/$var.calc_
RES=$ResDir/$var/$var.res

if [ -f $RES -a -f $CALC ]; then

   mv $CALC $ResDir/$var/$var.calc

fi

i=`echo "$i+1" | bc -lq`

done < "$input"

rm TempfileGID.tmp
