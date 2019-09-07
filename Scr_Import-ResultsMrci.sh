#!/bin/bash

Expfile1=$1

Expfile2=$2

Expfile3=$3

./PESMan.py import -e $Expfile1

./PESMan.py import -e $Expfile2

./PESMan.py import -e $Expfile3

echo -e "Import of data done!"

echo -e "\nNow deleting wfu files of mrci jobs..."

GeomDir=GeomData

find $GeomDir -name "mrci*wfu*" -type f -delete

echo -e "Wfu files of mrci jobs deleted!"

ResDir="Result_files_Mrci"

echo -e "\nNow creating Result files in "$ResDir"/..."

Dir1="$ResDir"

mkdir -p $Dir1/Prev

mv $Dir1/*dat $Dir1/Prev/

echo -e "\nObtaining results in "$Dir1"/..."

python ReadResultsMrci.py

echo -e "Results extracted in "$Dir1"/!"

#
exit 0

