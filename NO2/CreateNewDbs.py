#!/usr/bin/python
# -*- coding: utf-8 -*-

# The schema for format of new data base for main data base is as follows
sql_table_commands = """
BEGIN TRANSACTION;
CREATE TABLE Geometry(
Id INTEGER PRIMARY KEY,
Rho REAL,
Phi REAL,
Tags TEXT,
Desc TEXT, NNId Integer, NNId1 Integer, NNId2 Integer, Nnbr TEXT);
CREATE TABLE CalcInfo(
Id INTEGER PRIMARY KEY,
Type TEXT NOT NULL,
Name TEXT NOT NULL,
Depends INTEGER NOT NULL,
InpTempl TEXT NOT NULL,
OrbRec TEXT NOT NULL,
ResVars TEXT NOT NULL,
Desc TEXT);
CREATE TABLE Calc(
Id INTEGER PRIMARY KEY,
GeomId INTEGER NOT NULL,
CalcId INTEGER NOT NULL,
Dir TEXT NOT NULL,
WfnFile TEXT NOT NULL,
OrbRec TEXT NOT NULL,
InputFile TEXT NOT NULL,
OutputFile TEXT NOT NULL,
ResultFile TEXT NOT NULL,
AuxFiles TEXT,
Results TEXT,
Desc TEXT);
CREATE TABLE ExpCalc(
ExpId INTEGER NOT NULL,
GeomId INTEGER NOT NULL,
CalcDir TEXT NOT NULL);
CREATE TABLE Exports(
Id INTEGER PRIMARY KEY,
Type INTEGER DEFAULT 0,
CalcType INTEGER NOT NULL,
NumCalc INTEGER DEFAULT 0,
Status INTEGER DEFAULT 0,
ExpDT DATETIME,
ExpDir TEXT,
ImpDT TEXT,
ImpGeomIds TEXT);
END TRANSACTION;
"""

# the schema for data base containing table NbrTable
sql_nbrtable_commands = """
BEGIN TRANSACTION;
CREATE TABLE NbrTable (GeomId INTEGER, NbrId INTEGER, Depth INTEGER, Dist REAL);
END TRANSACTION;
"""

# As can be seen, new DbMain has three more tables.
# Also, the form of old tables are altered a little bit.

# 'Exports' - this table keeps track of all exported calculations.
#             an open export is one whose results have not been imported.
# 'ExpCalc' - this tables keeps a list of exported jobs yet to be imported.
#
# 'NbrTable' - helps track neighbours of a given geometry.
#              this tables can be very large making the DB several MBs.
#              Therefore, it is better to not have this table here,
#              but in someother DB called DbNbr.
#              This is used for exports with depth > 3 or depth <=0.
#
# Further, the Geometry table now has fields NNId, NNId1, NNId2 which
# are geometry IDs of 3 nearest geoemtries to the given geometry.
# This is usually enough for most exports with depth=1 (default),
# or depth=2,3 ... for slightly more expanded search.

import sqlite3
import sys
import os.path
import geometry
import misc

def create_tables(dbfile,sql_script):

   assert (dbfile)
   assert (sql_script)
   assert (isinstance(dbfile, basestring) and isinstance(sql_script,basestring))
   assert (not os.path.exists(dbfile)) # dbfile must not exist

   # now open db file, this will create the new data base

   con = None
   try:
      con = sqlite3.connect(dbfile)
      cur = con.cursor()
      cur.executescript(sql_script)
      con.commit()

   except sqlite3.Error, e:
      if con:
        print e
        con.rollback()
      sys.exit(1)

   except:
      print('Unknown error')
      raise

   finally:
      if con:
        con.close()

   return


def create_nbr_info(dbmain, dbnbr):

   assert (dbmain)
   assert (dbnbr)
   assert (os.path.exists(dbmain))
   assert (os.path.exists(dbnbr))

   # open both db files
   conMain = sqlite3.connect(dbmain)
   conMain.row_factory = sqlite3.Row
   curMain = conMain.cursor()  
   conNbr = sqlite3.connect(dbnbr)
   conNbr.row_factory = sqlite3.Row
   curNbr = conNbr.cursor()  

   # construct all geometry objects from main database
   curMain.execute("SELECT * from Geometry")

   lgeom = []
   geom_row = curMain.fetchone()
   while geom_row:
      lgeom.append(geometry.Geometry(rho=geom_row["Rho"],phi=geom_row["Phi"],id=geom_row["Id"]))
      geom_row = curMain.fetchone()

   # all geometries constructed
   # for every geometry, first construct a list of all possbile nearby geometries
     
   for geom in lgeom:

         # obtain list of all geometries which are supposed to be near to this geometry
         rho = geom.rho
         phi = geom.phi
         curMain.execute('''select * from Geometry where
                           (rho between ? and ?) and
                           (phi between ? and ?)''', (rho-4.5,rho+4.5,\
                                                      phi-misc.ToRad(30.0),phi+misc.ToRad(30.0)))
         lrow = curMain.fetchall()
         lnear_all = [ geometry.Geometry(rho=row["Rho"],phi=row["Phi"],id=row["Id"]) for row in lrow if row["Id"] != geom.id ]

         # now sort this list in increasing order of distance from given geometry
         lnear_all.sort(key=lambda g: geom.distance(g))
         assert (lnear_all)

         # consider first thirty geometries into this list
         lgeom_near = lnear_all[0:min(30,len(lnear_all))]
         txt = ' '.join([str(i.id) for i in lgeom_near])

         # now add first three geometries to Geometry table
         assert(len(lgeom_near) >=3)
         curMain.execute('UPDATE Geometry SET NNId = ?, NNId1 = ?, NNId2 = ?, Nnbr=? where Id=?',\
                     (lgeom_near[0].id,lgeom_near[1].id,lgeom_near[2].id,txt,geom.id))

         # add all 30 to NbrTable
         curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)",\
              [(geom.id,lgeom_near[i].id,i,geom.distance(lgeom_near[i])) for i in range(len(lgeom_near))])

   # done, commit now
   conMain.commit()
   conNbr.commit()

   return

if __name__ == "__main__":

   
#==============================================================================
   import math
   import geometry
   import gengrid
#==============================================================================

   pi = math.pi

   dbfile = "no2db.db"

   # if dbfile does not exist, then create it and add tables into it
   if not os.path.exists(dbfile):
      create_tables(dbfile,sql_table_commands)

   # open the data base
   con = sqlite3.connect(dbfile)
   cur = con.cursor()

   # now add some data into tables
   # first add the asymptotic geometry point
   lrho = [0.0]
   lphi = [0.0]

   lgeom = gengrid.GenerateGrid(lrho,lphi)

   # now add some data into tables
   # first add a bunch of geometry data
   lrho = [(0.5 + 0.5*i) for i in range(10)]
   lphi = [(0.0 + 1.0*i)*pi/180.0 for i in range(181) ]

   llgeom = gengrid.GenerateGrid(lrho,lphi)

   lgeom.extend(llgeom)

   lpol = []
   for g in lgeom:
      (r,p) = g.to_polar()
      lpol.append((r,p,""))

   # now insert this into data base
   cur.executemany("""INSERT INTO Geometry (Rho,Phi,Tags) VALUES (?, ?, ?)""", lpol)

   # done successfully, now we test other things
   # this should be saved by now
   lgeom = []
   for row in cur.execute('SELECT Rho, Phi, Id FROM Geometry'):
      lgeom.append(geometry.Geometry(row[0],row[1],id=row[2]))

   ### add linear and pathlogical tags
   ##cur.executemany("""UPDATE Geometry SET Tags=? WHERE Id=?""",[(gengrid.geom_tags(g),g.id) for g in lgeom])

   # print the geometries currently listed in data base
   lgeom = []
   for row in cur.execute('SELECT Rho, Phi, Id FROM Geometry'):
      lgeom.append(geometry.Geometry(row[0],row[1],id=row[2]))

   f = open("geomdata.txt",'w')
   for g in lgeom:
      f.write(str(g))
      f.write("\n")
   f.close()

   con.commit()
   con.close()

   dbnbr = "no2db-nbr.db"

   # if dbnbr does not exist, then create it and add tables into it
   if not os.path.exists(dbnbr):
      create_tables(dbnbr,sql_nbrtable_commands)

   create_nbr_info(dbfile, dbnbr)

   # done successfully

   

