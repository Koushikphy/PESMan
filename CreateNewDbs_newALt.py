# The schema for format of new data base for main data base is as follows
import os
import time
import sqlite3
import numpy as np
from geometry import geomObj
from multiprocessing import Pool



sql_table_commands = """
BEGIN TRANSACTION;
CREATE TABLE Geometry(
Id INTEGER PRIMARY KEY,
sr REAL,
cr REAL,
theta REAL,
Tags TEXT,
Desc TEXT, Nbr TEXT);
CREATE TABLE CalcInfo(
Id INTEGER PRIMARY KEY,
Type TEXT NOT NULL,
InpTempl TEXT NOT NULL,
OrbRec TEXT NOT NULL,
Desc TEXT);
CREATE TABLE Calc(
Id INTEGER PRIMARY KEY,
GeomId INTEGER NOT NULL,
CalcId INTEGER NOT NULL,
Dir TEXT NOT NULL,
OrbRec TEXT NOT NULL,
AuxFiles TEXT,
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
CREATE TABLE Results(
GeomId INTEGER NOT NULL,
CalcId INTEGER NOT NULL,
Results TEXT NOT NULL);
END TRANSACTION;
"""






def kabsch(p, q):
    c = np.dot(np.transpose(p), q)
    v, s, w = np.linalg.svd(c)
    d = (np.linalg.det(v) * np.linalg.det(w)) < 0.0

    if d:
        s[-1] = -s[-1]
        v[:, -1] = -v[:, -1]
    return  np.dot(v, w)


def calc_rmsd(p,q):
    p -= sum(p)/len(p) #np.mean(p, axis=0)
    q -= sum(q)/len(q) #np.mean(q, axis=0)
    p = np.dot(p, kabsch(p, q))
    return np.sqrt(np.sum((p-q)**2)/p.shape[0])



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
    cJac   = geomObj.getCart(*geom[1:])
    lkabsh = np.array([calc_rmsd(cJac, geomObj.getCart(*i[1:]))  for i in vGeom])
    index = lkabsh.argsort()[:lim]
    txt = ' '.join([str(i) for i in vGeom[index,0]])

    return geom[0], txt




if __name__ == "__main__":
    dbfile = "fh2dbaltmult.db"
    dbExist = os.path.exists(dbfile)
    con = sqlite3.connect(dbfile)

    try:
        with con:  # the context manager commits and rolls back in exception for us.
            if dbExist:
                con.executescript(sql_script) 
            curMain = conM.cursor()

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
                curMain.execute('select sr,cr,theta from geometry')
                oldTable = np.array(curMain.fetchall())
                dupInd = np.any(np.isin( oldTable, newGeomList), axis=1)
                if dupInd.size:
                    print("%s duplicates found in new list of geometries"%dupInd.size)
                    newGeomList = np.delete(newGeomList, np.where(dupInd), axis=0) # delete duplicates



            assert newGeomList.size, "No new geometries to add"
            # create the tags
            # tags = np.apply_along_axis(geomObj.geom_tags, 1, newGeomList)
            # # insert the geometries and tags into database
            # curMain.executemany("""INSERT INTO Geometry (sr,cr,theta,tags) VALUES (?, ?, ?,?)""", np.column_stack([ newGeomList, tags]))


            #get the updated table
            curMain.execute('select id,sr,cr,theta from geometry')
            geomList= np.array(curMain.fetchall())

            np.savetxt("geomdata.txt", geomList, fmt=['%d', '%.8f', '%.8f', '%.8f'], delimiter='\t')

            # Create a pool of workers on all processors of system and feed all the functions (synchronously ???)
            pool = Pool()
            dat = pool.map(getKabsch, geomList)
            curMain.executemany('UPDATE Geometry SET Nbr = ? where Id=?', dat)


    except Exception as e:
        print("Something went wrong. %s"%e)
    finally :
        con.close()
