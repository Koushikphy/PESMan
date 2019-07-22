#!/bin/bash

Expfile1=$1
Expfile2=$2
Expfile3=$3

./PESMan.py import -e $Expfile1

./PESMan.py import -e $Expfile2

./PESMan.py import -e $Expfile3

echo -e "Import of data done!"

echo -e "\nNow deleting wfu files of nact jobs..."

GeomDir=GeomData

find $GeomDir -name "multinact*wfu*" -type f -delete

echo -e "Wfu files of nact jobs deleted!"

ResDir="Result_files_Nact"

mkdir -p $ResDir

echo -e "\nNow creating Result files in "$ResDir"/..."

Dir1=$ResDir/TAU-RHO
Dir2=$ResDir/TAU-THETA
Dir3=$ResDir/TAU-PHI
Dir4=$ResDir/TAU

mkdir -p $Dir1
mkdir -p $Dir2
mkdir -p $Dir3
mkdir -p $Dir4
mkdir -p $Dir1/Prev
mkdir -p $Dir2/Prev
mkdir -p $Dir3/Prev
mkdir -p $Dir4/Prev

mv $Dir1/*dat $Dir1/Prev/
mv $Dir2/*dat $Dir2/Prev/
mv $Dir3/*dat $Dir3/Prev/
mv $Dir4/*dat $Dir4/Prev/

python ReadResultsNacts.py

echo -e "\nResults extracted from database and written."

exit 0

