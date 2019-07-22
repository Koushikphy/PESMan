#!/bin/bash

#To exit the script as soon as one of the commands failed
#--------------------------------------------------------
set -e                     
#--------------------------------------------------------

export PYTHONPATH=/home/bijit/KOUSHIK/Python-2.7.16/Lib/site-packages/lib/python2.7/site-packages/

export pynum=/home/bijit/KOUSHIK/Python-2.7.16/python

ResDir="$PWD/Result_files_Multi"

PESDir="$PWD/GeomData"

RunDir="$PWD/RunDir"                      #do not put '/' at the end of any path

mkdir -p $RunDir

mkdir -p $ResDir

touch $ResDir/tmp.dat

ndir=`ls $PESDir | wc -l`

#Give NN the no. of exports to be made!!!

NN=3000

#Give the latest no. of export for the value of I. Consult "Exports" table of the main database for the correct number.

I=6427


ndir1=`ls $PESDir | wc -l`

N=`echo "$I+$NN" | bc -lq`

while [ "$I" -lt "$N" ]
do

  fl=0

  $pynum PESMan.py export -j 1 --calc-id 1 --depth 0 2>> error_export.log

  extcd=$?
 
  if [ "$extcd" -ne 0 ] 
  then

    echo "Error in PESMan export"
    fl=1
    break             #Its better to break if an error occurs in exporting jobs..

  fi

  I=`echo "$I+1" | bc -lq`

  CJDir=Export$I-multi1

  # Check whether null export happened. If null export then exit...

  ndexp=`ls ExpDir/$CJDir | wc -l`

  if [ "$ndexp" -lt 3 ]; then

     echo -e "No export done. Try increasing the depth.\n"

     echo -e "Exiting now...\n"

     #-------------------------------------------------------
     # Reading results done before exiting 
     #-------------------------------------------------------

     mkdir -p $ResDir/Prev

     mv $ResDir/*dat $ResDir/Prev/

     echo -e "\nObtaining results in "$ResDir"..."

     python ReadResultsMulti.py

     echo -e "Results extracted in "$ResDir"..."

     #-------------------------------------------------------
     # Reading results end here 
     #-------------------------------------------------------

     exit 1

  fi

  echo -e "Sending export files to $RunDir...\n"

  cp -r ExpDir/$CJDir $RunDir

  echo -e "Molpro of Exported Job $CJDir running...\n"

  cd $RunDir/$CJDir/

  $pynum RunJob$I.py

  extcd=$?
 
  if [ "$extcd" -ne 0 ] 
  then

    echo "Error in Job execution of $CJDir"

    break             #Its better to break if an error occurs in executing jobs..

  fi

  cd -

  echo -e "Job executed...\n"

  echo -e "Moving files from $RunDir...\n"

  mv $RunDir/$CJDir ImpDir/

  if [ -f TempfileGID.tmp ]; then

  rm -f TempfileGID.tmp

  fi

  $pynum PESMan.py import -e ImpDir/$CJDir/export.dat 2>> error_import.log

  extcd=$?

  if [ "$extcd" -ne 0 ]; then

     echo "Error in PESMan import"

     fl=1

     break

  fi 

  rm -rf ExpDir/$CJDir

   ndir2=`ls $PESDir | wc -l`

   #-------------------------------------------------------
   # Reading results start every after 25 iterations
   #-------------------------------------------------------

   if [ `echo "$I % 25" | bc` -eq 0 ];then

     mkdir -p $ResDir/Prev

     mv $ResDir/*dat $ResDir/Prev/

     echo -e "\nObtaining results in "$ResDir"..."

     python ReadResultsMulti.py

     echo -e "Results extracted in "$ResDir"..."

   fi

   #-------------------------------------------------------
   # Reading results end here 
   #-------------------------------------------------------

done

#

if [ "$fl" -eq 1 ]
then

  echo "Script RunManager terminated due to the above error!!!"
  
  exit 1

else

  echo "Script RunManager successfully executed."

fi

#-------------------------------------------------------
# Reading results done at the end of the script
#-------------------------------------------------------

mkdir -p $ResDir/Prev

mv $ResDir/*dat $ResDir/Prev/

echo -e "\nObtaining results in "$ResDir"..."

python ReadResultsMulti.py

echo -e "Results extracted in "$ResDir"..."

#-------------------------------------------------------
# Reading results end here 
#-------------------------------------------------------

echo -e "\nPresent no. of Multi calculations = "$ndir2

echo -e "\nTotal no. of Multi calculations included in this run = "`echo "$ndir2-$ndir1" | bc -lq`

echo -e "\nFor next run give the value of I as :"$I

