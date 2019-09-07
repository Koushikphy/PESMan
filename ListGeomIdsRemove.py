#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
import os.path
import ExtractGeomIDs

def GetImpDirList(ImpDir,bManual):

    if not bManual:

      assert (os.path.exists(ImpDir))

      lDir=os.listdir(ImpDir)
      lg=[]

      for elem in lDir:
        if elem[0:7] == 'multi1-' or elem[0:6] == 'mrci2-' or elem[0:9] == 'ananact2-':
          sGID = elem.split("-")[1][4:]
          sID = elem.split("-")[2]
          lg.append((int(sID),sGID,elem))

      lg.sort()
      ll = []
    
      for el in lg:
        sid,sgid,selem = el
        ll.append(selem)

    else:

#     ll=[]

#     for i in range(45):
#        gid = 12559 + 91*i
#        for j in range(10):
#          ll.append(gid)
#          gid += 1 

      ll = range(1136,1140) + [1054,1055] + range(1084,1088) 
      ll += range(993,996) + range(1022,1028) 

    f=open("TempfileGID.tmp","a") 
    for x in ll:
      f.write(str(x)+"\n")

    f.close()
 
    return


if __name__ == "__main__":

   #dbmain = "fh2db.db"
   #ExtractGeomIDs.DoneGeomIDs(dbmain)

   ImpDir=""
   #GetImpDirList(ImpDir,bManual=False)
   GetImpDirList('',bManual=True)

