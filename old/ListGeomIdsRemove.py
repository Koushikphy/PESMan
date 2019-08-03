#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
import os.path

def GetImpDirList(ImpDir,bManual):

    if bManual:

      assert (os.path.exists(ImpDir))

      lDir=os.listdir(ImpDir)
      lg=[]

      for elem in lDir:
        if elem[0:11] == 'multinact2-':
          sGID = elem.split("-")[1][4:]
          sID = elem.split("-")[2]

          if len(sID) == 1:
            sID = '0'+'0'+ sID
          elif len(sID) == 2:
            sID = '0' + sID
 
          lg.append((sID,sGID))

      lg.sort()
      ll = []

      for el in lg:
        sid,sgid = el
        ll.append(int(sgid))

    else:

      ll = []

    f=open("TempfileGID.tmp","a") 
    for x in ll:
      f.write(str(x)+"\n")

    f.close()
 
    return


if __name__ == "__main__":

   ImpDir="/home/bijit/SOUMYA/TRIFLUOROBENZENE/PAIRWISE-CALC/9X-9Y/PESMan/ImpDir/Export3056-multinact2"
   GetImpDirList(ImpDir,bManual=True)

