#!/bin/bash

if [ -f TempfileGID.tmp ]; then

rm TempfileGID.tmp

fi

JobDir=$1
Cores=2
ScrDir='~/MOLPRO_SCRATCH'
#ScrDir='/tmp/bijit'

if [ -f $JobDir/Runjob.sh ]; then

rm $JobDir/Runjob.sh

fi

echo -e "#!/bin/bash\n" >> $JobDir/Runjob.sh

echo "echo \"******************************************************************\" >> run.log" >> $JobDir/Runjob.sh

echo "dt=\$(date '+%d/%m/%Y %H:%M:%S');" >> $JobDir/Runjob.sh

echo "echo \"                          \"\$dt\"                                \" >> run.log" >> $JobDir/Runjob.sh

echo "echo -e \"******************************************************************\n\" >> run.log" >> $JobDir/Runjob.sh

echo -e "\n" >> $JobDir/Runjob.sh

./ExtractGeomIDs.py $JobDir

# "ExtractGeomIds.py" generates file "TempfileGID.tmp" containing the directory names

# To read the directory names from the "tmp" file
input="TempfileGID.tmp"

while IFS='' read -r var || [[ -n "$var" ]]; do

Inpfile=$var.com

Wfufile=$var.wfu

echo "dt=\$(date '+%d/%m/%Y %H:%M:%S');" >> $JobDir/Runjob.sh

echo "echo \"Begin job "$var" on \"\$dt\"\" >> run.log" >> $JobDir/Runjob.sh

echo "cd "$var"" >> $JobDir/Runjob.sh

echo "cp "$Wfufile" "$ScrDir"" >> $JobDir/Runjob.sh

echo "molpro -d "$ScrDir" -W . -n "$Cores" "$Inpfile"" >> $JobDir/Runjob.sh

echo "exitcode=\$?" >> $JobDir/Runjob.sh

echo "rm -rf "$ScrDir"/"$Wfufile"" >> $JobDir/Runjob.sh

echo "cd ../" >> $JobDir/Runjob.sh

echo "dt=\$(date '+%d/%m/%Y %H:%M:%S');" >> $JobDir/Runjob.sh

echo "if [ \$exitcode -eq 0 ]" >> $JobDir/Runjob.sh

echo "then" >> $JobDir/Runjob.sh

echo "  echo -e \"  Completed on \"\$dt\"\n\" >> run.log" >> $JobDir/Runjob.sh

echo "  mv "$var"/"$var".calc_  "$var"/"$var".calc" >> $JobDir/Runjob.sh

echo "else" >> $JobDir/Runjob.sh

echo "  echo -e \"  JOB UNSUCCESSFUL ON \"\$dt\"\n\" >> run.log" >> $JobDir/Runjob.sh

echo "fi" >> $JobDir/Runjob.sh

echo -e "\n" >> $JobDir/Runjob.sh

done < "$input"

echo "echo -e \"\nAll jobs done!\n\" >> run.log" >> $JobDir/Runjob.sh

chmod +x $JobDir/Runjob.sh

rm TempfileGID.tmp

