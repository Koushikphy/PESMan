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
from multiprocessing import Pool

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


def jac2cart(geom):

    # the first element of geom is actually geom id, so just skip it here, well, i know this is bad.
    rs, rc, gamma = geom
    # gamma = np.deg2rad(gamma) # should I convert it here or is it already in radian in table????
    f1y = rc*np.sin(gamma)
    f1z = rc*np.cos(gamma)
    h2y = 0.0
    h2z = -rs/2.0
    h3y = 0.0
    h3z = rs/2.0
    return  np.array([[f1y,f1z], [h2y,h2z], [h3y,h3z] ])


def geom_tags(geom):
    """ generate tags for geometry """
    theta = geom[2]
    dat = jac2cart(geom)
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


def create_tables(dbfile,sql_script, main=False):

    if main:  # main database
        if os.path.exists(dbfile) :
            return 
    else :   # neighbour database
        if os.path.exists(dbfile) :
            os.remove(dbfile)

    # now open db file, this will create the new data base
    con = sqlite3.connect(dbfile)
    try:
        with con: # the context manager commits and rolls back in exception for us.
            con.executescript(sql_script) 
    except Exception as e:
        print e
    con.close()



# cartGeom is function that convert the geometry defined in normal mode/hyperspherical/jacobi to cartesian
# here the grid is in Jacobi, so jac2cart
cartGeom = jac2cart


def getKabsch(geom, lim=10):
    # the geomList has to be available on global scope, so that the pool worker threads can access it
    vGeom = geomList[np.where( 
                    (geomList[:,1] > geom[1]-4.5) & 
                    (geomList[:,1] < geom[1]+4.5) &
                    (geomList[:,2] > geom[2]-30)  &
                    (geomList[:,2] < geom[2]+30)  &
                    (geomList[:,3] > geom[3]-np.deg2rad(50.0)) & 
                    (geomList[:,3] < geom[3]+np.deg2rad(50.0)) &
                    (geomList[:, 0] != geom[0])
                    )]
    cJac   = cartGeom(geom[1:])
    lkabsh = np.array([calc_rmsd(cJac, cartGeom(i[1:]))  for i in vGeom])
    index  = lkabsh.argsort()[:lim]


    return [geom[0], vGeom[index,0], lkabsh[index]]




if __name__ == "__main__":
    start = time.time()
    dbfile = "fh2dbaltmult.db"
    dbnbr = "fh2db-nbraltmult.db"

    # is it firstime the database is created? Some checks are not needed here
    dbExist = os.path.exists(dbfile)

    create_tables(dbfile, sql_table_commands, main = True)
    create_tables(dbnbr, sql_nbrtable_commands)

    conMain = sqlite3.connect(dbfile)
    curMain = conMain.cursor()

    conNbr = sqlite3.connect(dbnbr)
    curNbr = conNbr.cursor()


    lsr = [1.445]
    lcr = [(3.0 + 0.1*i) for i in range(300)]
    lthe = [0.0]
    # index order correct ?
    newGeomList = np.dstack(np.meshgrid(lsr, lcr, lthe, indexing='ij')).reshape(-1,3)
    # newGeomList = np.vstack([[0,0,0], newGeomList])

    #########################################################################################
    # newGeomList = np.array([]).reshape(0,3)

    # lsr = [1.445]
    # lcr = [(3.0 + 0.1*i) for i in range(20)]
    # lthe = [0.0]
    # geomListToAdd =  np.dstack(np.meshgrid(lsr, lcr, lthe, indexing='ij')).reshape(-1,3)  # create a 2D array of the geometries
    # newGeomList = np.vstack([newGeomList, geomListToAdd])                                 # stack the array to geomlist

    # # adding a single point?
    # lsr = [1.445]
    # lcr = [0]
    # lthe = [0.0]
    # geomListToAdd =  np.dstack(np.meshgrid(lsr, lcr, lthe, indexing='ij')).reshape(-1,3)
    # newGeomList = np.vstack([newGeomList, geomListToAdd])

    # # the above approach works, but as it's just a single point, we don't have to go through this much to create a meshgrid
    # # just stack the single point
    # newGeomList = np.vstack([[1.445,0,0], newGeomList])
    ######################################################################




    if dbExist: # if it does exists then check if any duplicate geometry is being passed
        print("here")
        curMain.execute('select sr,cr,theta from geometry')
        oldTable = np.array(curMain.fetchall())
        dupInd = np.any(np.isin( oldTable, newGeomList), axis=1)
        if dupInd.size:
            print("%s duplicates found in new list of geometries"%dupInd.size)
        newGeomList = np.delete(newGeomList, np.where(dupInd), axis=0) # delete duplicates

    assert newGeomList.size, "No new geometries to add"
    # create the tags
    tags = np.apply_along_axis(geom_tags,1, newGeomList)
    # insert the geometries and tags into database
    curMain.executemany("""INSERT INTO Geometry (sr,cr,theta,tags) VALUES (?, ?, ?,?)""", np.column_stack([ newGeomList, tags]))


    #get the updated table
    curMain.execute('select id,sr,cr,theta from geometry')
    geomList= np.array(curMain.fetchall())

    np.savetxt("geomdata.txt", geomList, fmt=['%d', '%.8f', '%.8f', '%.8f'], delimiter='\t')

    # Create a pool of workers on all processors of system and feed all the functions (synchronously ???)
    pool = Pool()
    dat = pool.map(getKabsch, geomList)
    for idd, vGeom,lkabsh in dat:
        curMain.execute('UPDATE Geometry SET NNId = ?, NNId1 = ?, NNId2 = ? where Id=?', [vGeom[0],vGeom[1],vGeom[2],idd])
        curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)", [[idd, vGeom[i], i, lkabsh[i]] for i in range(vGeom.shape[0])])


    conMain.commit()
    conMain.close()
    conNbr.commit()
    conNbr.close()
    print time.time() -start
