# The schema for format of new data base for main data base is as follows
import os
import sqlite3
import numpy as np
from multiprocessing import Pool
from ConfigParser import SafeConfigParser


sql_script = """
BEGIN TRANSACTION;
CREATE TABLE Geometry(
Id INTEGER PRIMARY KEY,
rho REAL,
phi REAL,
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



r30 = np.deg2rad(30)
lim = 30

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
    # takes two cartesian geometries p and q
    p -= sum(p)/len(p) #np.mean(p, axis=0)
    q -= sum(q)/len(q) #np.mean(q, axis=0)
    p = np.dot(p, kabsch(p, q))
    return np.sqrt(np.sum((p-q)**2)/p.shape[0])



def distance(xy1, xy2):
    return np.sqrt((xy1[0] - xy2[0])**2 + (xy1[1] - xy2[1])**2)


def getKabsch(geom, lim=lim):
    #accessing the full geomList from the global scope
    # WARNING !!! Do not use this approach in windows systems, windows doesn't uses fork to spawn child processes
    vGeom = geomList[np.where( 
                    (geomList[:,1]  >= geom[1]-4.5) &
                    (geomList[:,1]  <= geom[1]+4.5) &
                    (geomList[:,2]  >= geom[2]-r30) &
                    (geomList[:,2]  <= geom[2]+r03) &
                    (geomList[:, 0] != geom[0])
                    )]
    lkabsh = np.array([distance(geom[3:], i[3:])  for i in vGeom])
    index = lkabsh.argsort()[:lim]

    return geom[0], vGeom[index,0].astype(np.int64), lkabsh[index]



# WARNING!!! Do not pollute the module level namespace while using multiprocessing module
if __name__ == "__main__":
    scf = SafeConfigParser()
    scf.read('pesman.config')
    dbFile = scf.get('DataBase', 'db')
    nbrDbFile = scf.get('DataBase', 'Nbr')       # nbr db, not going to be used in any calculations
    dbExist = os.path.exists(dbFile)

    if dbExist:    # remove old db if you want
        os.remove(dbFile)
        dbExist = False
    if os.path.exists(nbrDbFile):    # mandatoryly remove nbr db
        os.remove(nbrDbFile)


    with sqlite3.connect(dbFile) as con, sqlite3.connect(nbrDbFile) as conNbr:
        if not dbExist:
            cur = con.cursor()
            cur.executescript(sql_script)

        curNbr = conNbr.cursor()
        curNbr.executescript(sql_nbrtable_commands)

        newGeomList = np.dstack(np.mgrid[0.1:5.0:50j,0:180:181j]).reshape(-1,2)
        newGeomList = np.vstack([[0,0], newGeomList])
        newGeomList[:,1] = np.deg2rad(newGeomList[:,1])


        # if db exists then check if any duplicate geometry is being passed, if yes, then remove it
        if dbExist: 
            cur.execute('select rho,phi from geometry')
            oldTable = np.array(cur.fetchall())
            if oldTable.size:
                dupInd = np.any(np.isin( oldTable, newGeomList), axis=1)
                if dupInd.size:
                    print("%s duplicates found in new list of geometries"%dupInd.size)
                    newGeomList = np.delete(newGeomList, np.where(dupInd), axis=0) # delete duplicates



        assert newGeomList.size, "No new geometries to add"
        # # create any tags if necessary, use from geomObj are other functions whatever convenient
        # # tags = np.apply_along_axis(geomObj.geom_tags, 1, newGeomList)
        # # insert the geometries and tags into database
        cur.executemany('INSERT INTO Geometry (rho,phi) VALUES (?, ? )', newGeomList)

        # #get the updated table with ids
        cur.execute('select id,rho,phi from geometry')
        geomList= np.array(cur.fetchall())
        x = geomList[:,1]*np.cos(geomList[:,2])
        y = geomList[:,1]*np.sin(geomList[:,2])
        geomList = np.column_stack([ geomList, x, y])


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
        geomList[:,2] = np.rad2deg(geomList[:,2])
        np.savetxt("geomdata.txt", geomList[:,:3], fmt=['%d', '%.8f', '%.8f'], delimiter='\t')

