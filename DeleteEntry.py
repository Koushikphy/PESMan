#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os
import os.path

def DeleteCalcEntry(dbmain,TmpFile,calcid):
    
    assert (dbmain)
    assert (os.path.exists(dbmain))

    with open(TmpFile,'r') as f:
      sGIDs = f.read()
      f.close()

    llGIDs = sGIDs.split("\n")
    lGIDs = llGIDs[:len(llGIDs)-1]

    # open the database
    con = sqlite3.connect(dbmain)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    for GID in lGIDs:
      cur.execute("select * from calc where geomid = ? and calcid = ?",(int(GID),calcid))
      calc_row = cur.fetchall()
      if len(calc_row) == 0:
        raise Exception ("The entry with GeomId = %d and CalcId = %d not found in calc table"%(int(GID),calcid))
      else:
        cur.execute("delete from calc where geomid = ? and calcid = ?",(int(GID),calcid))

    # done, commit now
    con.commit()

    return

if __name__ == "__main__":

   dbmain = "h3db.db"
   TmpFile = "TempfileGID.tmp"
   #TmpFile = "TempfileGIDNact.tmp"

   calcid = sys.argv[1]

   calcid = int(calcid)

   assert (calcid > 0 and calcid <=3)

   DeleteCalcEntry(dbmain,TmpFile,calcid)

