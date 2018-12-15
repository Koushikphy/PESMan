#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import misc

def ParseFile(sfile,lkeys):
   """ A generic parser which can parse key : value pairs from any string and return a dictionary of parsed options """
   def remove_comments(s):
       p = s.find("#")
       if p >=0:
          snew = s[0:p]
       else:
          snew = s
       return snew.strip()
   ls0 = [x.strip() for x in sfile.splitlines() if x.strip()]
   ls1 = [tuple(x.split(":")) for x in ls0 if remove_comments(x)]
   for t in ls1:
      assert (len(t) == 2)
   ls2 = [(x.strip(),y.strip()) for (x,y) in ls1]
   lparse = { k.upper():v for (k,v) in ls2 }
   for key in lkeys:
      assert( key.upper() in lparse )
   assert (len(lparse) == len(lkeys))
   return lparse

def AddNewCalcType(db,conf):
   """ Add a new calculation type into the database
       db    -- data base file
       conf  -- config file specifying the calculation
       NOTE : all file names must be fully qualified. they are simply opened.
   """
   # first parse the conf files
   templ = None
   misc.CheckFileAccess(conf,True,True)
   with open(conf,'r') as f:
      sconf = f.read()
      f.close()
      tconf = ParseFile(sconf,["name","type","depends","template","record","resvars","desc"])
      # checks on the sanity of config file
      tconf["NAME"] = tconf["NAME"].lower()
      tconf["TYPE"] = tconf["TYPE"].lower()
      ##assert (tconf["TYPE"] in ["multi", "mrci", "multinact","ddrnact"])
      tconf["DEPENDS"] = tconf["DEPENDS"].lower()
      assert (tconf["DEPENDS"] == "none" or tconf["DEPENDS"].isdigit())
      if tconf["DEPENDS"] == "none":
         tconf["DEPENDS"] = 0
      else:
         tconf["DEPENDS"] = int(tconf["DEPENDS"])
      templ = tconf["TEMPLATE"]
      assert(templ)
      lrec = tconf["RECORD"].split(".",1)
      assert (len(lrec) == 2 and lrec[0].isdigit() and lrec[1].isdigit())
      rec,fil = int(lrec[0]),int(lrec[1])
      tconf["RECORD"] = str(rec) + "." + str(fil)
      # desc and resvars are unchanged, used later

   # open templ file defined previously
   misc.CheckFileAccess(templ,bRead=True,bAssert=True)
   with open(templ,'r') as f:
      stemp = f.read()
      f.close()

   # now we are ready to open the data base and add record to CalcInfo table
   misc.CheckFileAccess(db,bRead=True,bAssert=True)
   with sqlite3.connect(db) as con:
      # define cursor, data base opening errors are taken care automatically
      cur = con.cursor()
      for n in cur.execute('SELECT Name from CalcInfo'):
         assert( tconf["NAME"] != n[0] )
      tcalc = (tconf["TYPE"],tconf["NAME"],tconf["DEPENDS"],stemp,tconf["RECORD"],tconf["RESVARS"],tconf["DESC"])
      cur.execute("""INSERT INTO CalcInfo (Type,Name,Depends,InpTempl,OrbRec,ResVars,Desc) VALUES (?, ?, ?, ?, ?, ?, ?)""", tcalc)
      # now we are done, release
      con.commit()
      # check if it is inserted properly
      for row in cur.execute("SELECT * FROM CalcInfo"):
         print row
      print "record inserted and closed"



if __name__ == "__main__":

     db = "h3db.db"

     conf = "calc.config"

     AddNewCalcType(db,conf)
     conf = "cicalc.config"

     AddNewCalcType(db,conf)




