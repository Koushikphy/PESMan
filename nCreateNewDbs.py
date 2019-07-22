#!/usr/bin/python
# -*- coding: utf-8 -*-

# The schema for format of new data base for main data base is as follows
sql_table_commands = """
BEGIN TRANSACTION;
CREATE TABLE Geometry(
Id INTEGER PRIMARY KEY,
sr REAL,
cr REAL,
theta REAL,
Tags TEXT,
Desc TEXT, NNId Integer, NNId1 Integer, NNId2 Integer);
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
CREATE TABLE Results(
GeomId INTEGER NOT NULL,
CalcId INTEGER NOT NULL,
Energy TEXT NOT NULL,
Somatel TEXT NOT NULL,
Soener TEXT NOT NULL);
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


import os
import time
import sqlite3
import numpy as np


def kabsch(p, q):
    c = np.dot(np.transpose(p), q)
    v, s, w = np.linalg.svd(c)
    d = (np.linalg.det(v) * np.linalg.det(w)) < 0.0

    if d:
        s[-1] = -s[-1]
        v[:, -1] = -v[:, -1]
    # create rotation matrix u
    return  np.dot(v, w)


def calc_rmsd(p,q):
    p -= sum(p)/len(p) #np.mean(p, axis=0)
    q -= sum(q)/len(q) #np.mean(q, axis=0)
    p = np.dot(p, kabsch(p, q))
    return np.sqrt(np.sum((p-q)**2)/p.shape[0])


def jac2cart(geomData):

    # the first element of geomData is actually geom id, so just skip it here, well, i know this is bad.
    _, rs, rc, gamma = geomData
    # gamma = np.deg2rad(gamma) # should I convert it here or is it already in radian in table????
    f1y = rc*np.sin(gamma)
    f1z = rc*np.cos(gamma)
    h2y = 0.0
    h2z = -rs/2.0
    h3y = 0.0
    h3z = rs/2.0
    return  np.array([[f1y,f1z], [h2y,h2z], [h3y,h3z] ])


def geom_tags(geomData):
    """ generate tags for geometry """
    theta = geomData[3]
    dat = jac2cart(geomData)
    # dat -> f,h,h and dat[[1, 2, 0]] -> h,h,f
    # so dists are distances of fh, hh, fh
    tmpdat = dat[[1, 2, 0]] - dat
    dists  = np.sqrt(np.sum(tmpdat**2, axis=1))

    path    = np.any(dists < (0.6/0.529177209)) #0.6 bohrs
    channel = np.abs(dists[0] + dists[2] - dists[1]) < 1.0e-10
    linear  = np.abs(theta) < 1.0e-10

    l = []
    if linear:   # linear position
        l.append("linear")
        if channel:
            l.append("Finside")
        else:
            l.append("Foutside")
    if path:
        l.append("path")
    return ":".join(l)


def create_tables(dbfile,sql_script):

    # delete dbfile if exists
    if os.path.exists(dbfile): os.remove(dbfile)

    # now open db file, this will create the new data base
    con = sqlite3.connect(dbfile)
    try:
        with con: # the context manager commits and rolls back in exception for us.
            con.executescript(sql_script) 
    except Exception as e:
        print e
    con.close()



def fillDataTables(dbmain, dbnbr, geomList):
    conMain = sqlite3.connect(dbmain)
    curMain = conMain.cursor()

    conNbr = sqlite3.connect(dbnbr)
    curNbr = conNbr.cursor()
    # start = time.time()

    curMain.executemany("""INSERT INTO Geometry (sr,cr,theta) VALUES (?, ?, ?)""", geomList)

    # add a column just as the id of the table
    geomList = np.column_stack([np.arange(1, geomList.shape[0] + 1), geomList])

    curMain.executemany("""UPDATE Geometry SET Tags=? WHERE Id=?""", [[geom_tags(i),i[0]] for i in geomList])
    np.savetxt("geomdata.txt", geomList, fmt=['%d', '%.8f', '%.8f', '%.8f'], delimiter='\t')


    ll = []
    c = 0
    for geom in geomList:
        start = time.time()
        vGeom = geomList[np.where( 
                        (geomList[:,1] > geom[1]-4.5) & 
                        (geomList[:,1] < geom[1]+4.5) &
                        (geomList[:,2] > geom[2]-30)  &    
                        (geomList[:,2] < geom[2]+30)  & 
                        (geomList[:,3] > geom[3]-np.deg2rad(50.0)) & 
                        (geomList[:,3] < geom[3]+np.deg2rad(50.0)) &
                        (geomList[:, 0] != geom[0])
                        )]
        cJac = jac2cart(geom)

        lkabsh = np.array([calc_rmsd(cJac, jac2cart(i))  for i in vGeom])
        indd   = lkabsh.argsort() [:10]
        lkabsh = lkabsh[indd]
        vGeom  = vGeom[indd,0]
        curMain.execute('UPDATE Geometry SET NNId = ?, NNId1 = ?, NNId2 = ? where Id=?', [vGeom[0],vGeom[1],vGeom[2],geom[0]])
        curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)", [[geom[0], vGeom[i], i, lkabsh[i]] for i in range(vGeom.shape[0])])

        ll.append(time.time()-start)
    print sum(ll)/len(ll)
    conMain.commit()
    conMain.close()
    conNbr.commit()
    conNbr.close()



if __name__ == "__main__":
    start = time.time()
    dbfile = "fh2dbalt.db"
    dbnbr = "fh2db-nbralt.db"

    create_tables(dbfile, sql_table_commands)
    create_tables(dbnbr,sql_nbrtable_commands)

    lsr = [1.445,1.447,1.449]
    lcr = [(3.0 + 0.1*i) for i in range(200)]
    lthe = [0.0]
    # index order correct ?

    geomList = np.dstack(np.meshgrid(lsr, lcr, lthe, indexing='ij')).reshape(-1,3)
    fillDataTables(dbfile, dbnbr, geomList)
    print time.time() -start



