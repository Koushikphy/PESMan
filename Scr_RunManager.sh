#!/bin/bash

#To exit the script as soon as one of the commands failed
#--------------------------------------------------------
set -e                     
#--------------------------------------------------------


PESDir="/home/bijit/F+H2/AB-INITIO/SURFACE/AB-INITIO/RHO_2.2/PESMan/GeomData"

RunDir="/home/bijit/F+H2/AB-INITIO/SURFACE/AB-INITIO/RHO_2.2/PESMan/RunDir"                      #do not put '/' at the end of any path

mkdir -p $RunDir

ResDir="/home/bijit/F+H2/AB-INITIO/SURFACE/AB-INITIO/RHO_2.2/PESMan/Result_files_Multi"

mkdir -p $ResDir

touch $ResDir/tmp.dat

ndir=`ls $PESDir | wc -l`

#Give NN the no. of exports to be made!!!

NN=1830

#Give the latest no. of export for the value of I. Consult "Exports" table of the main database for the correct number.

I=`sqlite3 no2db.db "SELECT id FROM exports ORDER BY id DESC LIMIT 1" `

ndir1=`ls $PESDir | wc -l`

N=`echo "$I+$NN" | bc -lq`

echo -e "\nMCSCF Iterations took place in files:" > IterMultiJobs.txt

echo    "------------------------------------" >> IterMultiJobs.txt

while [ "$I" -lt "$N" ]
do

  fl=0

  #./PESMan.py export -j 1 --calc-id 1 --depth 0 2>> error_export.log
  ./PESMan.py export -j 1 --calc-id 1 --depth 0 --incl-path 2>> error_export.log
  # python PESMan.py export -j 1 --calc-id 1 --depth 3 --constraint "tags like '%linear%'" --incl-path 2>> error_export.log

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

     echo -e "\nNow creating Result files in "$ResDir"/..."

     Dir1="$ResDir"

     mkdir -p $Dir1/Prev

     mv $Dir1/*dat $Dir1/Prev/

     echo -e "\nObtaining results in "$Dir1"/..."

     python ReadResultsMulti.py

     echo -e "Theta-phi results extracted in "$Dir1"/!"

     #-------------------------------------------------------
     # Reading results end here 
     #-------------------------------------------------------

     exit 1

  fi

  echo -e "Sending export files to $RunDir...\n"

  cp -r ExpDir/$CJDir $RunDir

  echo -e "Molpro of Exported Job $CJDir running...\n"

  cd $RunDir/$CJDir/

  ./RunJob$I.py

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

  python ExtractGeomIDs.py ImpDir/$CJDir

   # "ExtractGeomIds.py" generates file "TempfileGID.tmp" containing the geom ids or directory names

   # To read the geom ids from the "tmp" file
   input="TempfileGID.tmp"

   flag=0

   while IFS='' read -r var || [[ -n "$var" ]]; do

   #FILE=$PESDir/geom$var/multi1/multi1-geom$var.out

   #FILE1=multi1-geom$var.out
   FILE=ImpDir/$CJDir/$var/$var.out

   FILE1=$var.out

   NTR=`grep -B 2 "\*\* WVFN \*\*\*\*" $FILE |head -1 | awk '{print$1}'`

   # Only fetch those geoms whose multi itr has exceeded 38
   if [ "$NTR" -gt 38 ]; then

       echo $FILE1" of "$CJDir":  "$NTR >> IterMultiJobs.txt

       echo -e "\nThis job contains more than 38 multi iterations, hence cant be imported. Moving to next job..."

   else

       echo $FILE1" of "$CJDir":  "$NTR >> IterMultiJobs.txt

       python PESMan.py import -e ImpDir/$CJDir/export.dat 2>> error_import.log

       extcd=$?

       if [ "$extcd" -ne 0 ]; then

          echo "Error in PESMan import"

          fl=1

          break

       fi 

       rm -rf ExpDir/$CJDir

   fi
    
   done < "$input"

   rm -f TempfileGID.tmp
  
   ndir2=`ls $PESDir | wc -l`

   #-------------------------------------------------------
   # Reading results start every after 5 iterations
   #-------------------------------------------------------

   if [ `echo "$I % 5" | bc` -eq 0 ]
   then

       echo -e "\nNow creating Result files in "$ResDir"/..."

       Dir1="$ResDir"

       mkdir -p $Dir1/Prev

       mv $Dir1/*dat $Dir1/Prev/

       echo -e "\nObtaining results in "$Dir1"/..."
 
       python ReadResultsMulti.py

       echo -e "Theta-phi results extracted in "$Dir1"/!"

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

echo -e "\nNow creating Result files in "$ResDir"/..."

Dir1="$ResDir"

mkdir -p $Dir1/Prev

mv $Dir1/*dat $Dir1/Prev/

echo -e "\nObtaining results in "$Dir1"/..."

python ReadResultsMulti.py

echo -e "Theta-phi results extracted in "$Dir1"/!"

#-------------------------------------------------------
# Reading results end here 
#-------------------------------------------------------

echo -e "\nPresent no. of Multi calculations = "$ndir2

echo -e "\nTotal no. of Multi calculations included in this run = "`echo "$ndir2-$ndir1" | bc -lq`

echo -e "\nFor next run give the value of I as :"$I

