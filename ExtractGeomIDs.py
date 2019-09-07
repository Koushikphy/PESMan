#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
import os.path

""" This routine extracts geomids or filenames to be used
    by bash scripts that will extract other info e.g. no.
    of multi iterations, etc."""

def DoneGeomIDs(dbmain):
    
    assert (dbmain)
    assert (os.path.exists(dbmain))

    PESDir = "/home/bijit/F+H2/AB-INITIO/GLOBAL-CALCULATIONS/Initial-Calculations-Without-PESMan/GeomData"

    # open the database
    con = sqlite3.connect(dbmain)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("select geomid from calc")
    calc_row = cur.fetchall()

    for x in calc_row:
     
      f=open("TempfileGID.tmp","w")
      geomid = str(x["geomid"])
      f.write(geomid+"\n")
      f.close()
 
    # done, commit now
    con.commit()

    return

def GetImpDirList(ImpDir):

    assert (os.path.exists(ImpDir))

    lDir=os.listdir(ImpDir)
    ll=[]

    for elem in lDir:
      if elem[0:7] == 'multi1-' or elem[0:6] == 'mrci2-' or elem[0:11] == 'multinact3-':
        lx = elem.split('-')
        ll.append((int(lx[2]),lx[1],lx[0]))
       

    ll.sort()
    ldir=[]

    for i in ll:
      elem = i[2] + '-' + i[1] + '-' + str(i[0])
      ldir.append(elem)


    f=open("TempfileGID.tmp","w") 
    for x in ldir:
      f.write(x+"\n")

    f.close()
    
    return


if __name__ == "__main__":

   ImpDir = sys.argv[1]   
   GetImpDirList(ImpDir)

   #dbmain = "fh2db.db"
   #DoneGeomIDs(dbmain)

   #ImpDir="/home/bijit/F+H2/AB-INITIO/GLOBAL-CALCULATIONS/PESMan/ImpDir/Export28-multi1"
   #GetImpDirList(ImpDir)

