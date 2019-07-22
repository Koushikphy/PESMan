#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import os.path

def GetImpDirList(ImpDir):

    assert (os.path.exists(ImpDir))

    lDir=os.listdir(ImpDir)
    lg=[]

    for elem in lDir:
      if elem[0:7] == 'multi1-' or elem[0:11] == 'multinact2-':
        sGID = elem.split("-")[1][4:]
        sID = elem.split("-")[2]
        lg.append((int(sID),sGID,elem))

    lg.sort()
    ll = []
  
    for el in lg:
      sid,sgid,selem = el
      ll.append(selem)

    f=open("TempfileGID.tmp","a") 
    for x in ll:
      f.write(str(x)+"\n")

    f.close()
 
    return


if __name__ == "__main__":

   ImpDir = sys.argv[1]

   GetImpDirList(ImpDir)

