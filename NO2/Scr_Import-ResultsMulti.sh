#!/bin/bash

Expfile1=$1

#Expfile2=$2

#Expfile3=$3

#Expfile4=$4

./PESMan.py import -e $Expfile1

#./PESMan.py import -e $Expfile2

#./PESMan.py import -e $Expfile3

#./PESMan.py import -e $Expfile4

echo -e "Import of data done!"

ResDir="Result_files_Multi"

echo -e "\nNow creating Result files in "$ResDir"/..."

mkdir -p $ResDir/PREV

mv $ResDir/*dat $ResDir/PREV/

python ReadResultsMulti.py

echo -e "\nResults extracted from database and written."

