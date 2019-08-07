# The schema for format of new data base for main data base is as follows
import os
import sqlite3
import numpy as np
from geometry import geomObj
from multiprocessing import Pool



sql_script = """
BEGIN TRANSACTION;
CREATE TABLE Geometry(
Id INTEGER PRIMARY KEY,
sr REAL,
cr REAL,
gamma REAL,
Tags TEXT,
Nbr TEXT);
CREATE TABLE CalcInfo(
Id INTEGER PRIMARY KEY,
Type TEXT NOT NULL,
InpTempl TEXT NOT NULL,
Desc TEXT);
CREATE TABLE Calc(
Id INTEGER PRIMARY KEY,
GeomId INTEGER NOT NULL,
CalcId INTEGER NOT NULL,
Dir TEXT NOT NULL,
StartGId INTEGER NOT NULL,
Results TEXT);
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


sql_nbrtable_commands = """
BEGIN TRANSACTION;
CREATE TABLE NbrTable (GeomId INTEGER, NbrId INTEGER, Depth INTEGER, Dist REAL);
END TRANSACTION;
"""






def distance(xy1, xy2):
    return np.sqrt((xy1[0] - xy2[0])**2 + (xy1[1] - xy2[1])**2)


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

r50 = np.deg2rad(50)
lim = 30


def getKabsch(geom, lim=lim):
    #accessing the full geomList from the global scope
    # WARNING !!! Do not use this approach in windows systems, windows doesn't uses fork to spawn child processes
    vGeom = geomList[np.where( 
                    (geomList[:,2]  >= geom[2]-4.5) &
                    (geomList[:,2]  <= geom[2]+4.5) &
                    (geomList[:,3]  >= geom[3]-r50) &
                    (geomList[:,3]  <= geom[3]+r50) &
                    (geomList[:, 0] != geom[0])
                    )]
    cCart = geomObj.getCart(*geom[1:])
    lkabsh = np.array([calc_rmsd(cCart, geomObj.getCart(*i[1:])) for i in vGeom])
    index = lkabsh.argsort()[:lim]

    return geom[0], vGeom[index,0].astype(np.int64), lkabsh[index]



# WARNING!!! Do not pollute the module level namespace while using multiprocessing module
if __name__ == "__main__":
    dbFile = "heh2+db.db"
    nbrDbFile = 'heh2+db_nbr.db'       # nbr db, not going to be used in any calculations
    dbExist = os.path.exists(dbFile)
    if dbExist: os.remove(dbFile)    # remove old db if you want
    if os.path.exists(nbrDbFile):    # mandatoryly remove nbr db
        os.remove(nbrDbFile)

    # try:
    with sqlite3.connect(dbFile) as con, sqlite3.connect(nbrDbFile) as conNbr:
        cur = con.cursor()                 #<--- rmove this if db exists
        cur.executescript(sql_script)

        curNbr = conNbr.cursor()
        curNbr.executescript(sql_nbrtable_commands)

        newGeomList = np.stack( np.mgrid[2.0:2.0:1j, 0:10:101j, 0:90:19j], axis=3).reshape(-1,3)
        newGeomList[:,2] = np.deg2rad(newGeomList[:,2])
        # if db exists then check if any duplicate geometry is being passed, if yes, then remove it
        # if dbExist: 
        #     cur.execute('select rho,phi from geometry')
        #     oldTable = np.array(cur.fetchall())
        #     if oldTable.size:
        #         dupInd = np.any(np.isin( oldTable, newGeomList), axis=1)
        #         if dupInd.size:
        #             print("%s duplicates found in new list of geometries"%dupInd.size)
        #             newGeomList = np.delete(newGeomList, np.where(dupInd), axis=0) # delete duplicates



        assert newGeomList.size, "No new geometries to add"
        # # create any tags if necessary, use from geomObj are other functions whatever convenient
        tags = np.apply_along_axis(geomObj.geom_tags, 1, newGeomList)
        newGeomList = np.column_stack([newGeomList, tags])
        # # insert the geometries and tags into database
        cur.executemany('INSERT INTO Geometry (sr,cr,gamma,Tags) VALUES (?, ?, ?, ? )', newGeomList)

        # #get the updated table with ids
        cur.execute('select id,sr,cr,gamma from geometry')
        geomList= np.array(cur.fetchall())

        # Create a pool of workers on all processors of system and feed all the functions (synchronously ???)
        pool = Pool()
        dat = pool.map(getKabsch, geomList)
        for res in dat:
            gId = res[0]
            indexes = res[1]
            distances = res[2]

            cur.execute('UPDATE Geometry SET Nbr = ? where Id=?', (' '.join(map(str,indexes)), gId))
            curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)", [(gId, indexes[i], i, distances[i]) for i in range(lim)])

        # save the geomlist in a datafile
        geomList[:,3] = np.rad2deg(geomList[:,3])
        np.savetxt("geomdata.txt", geomList, fmt=['%d', '%.8f', '%.8f', '%.8f'], delimiter='\t')

    # except Exception as e:
    #     print("{}:{}".format(type(e).__name__, e))
