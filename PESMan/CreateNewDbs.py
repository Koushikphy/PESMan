# The schema for format of new data base for main data base is as follows
import os
import sqlite3
import numpy as np
from geometry import geomObj
from multiprocessing import Pool
from ConfigParser import SafeConfigParser


# Primarily written for a Jacobi system, modify likewise

sql_script = """
BEGIN TRANSACTION;
CREATE TABLE Geometry(
Id INTEGER PRIMARY KEY,
rho REAL,
theta REAL,
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
CalcId INTEGER NOT NULL,
GeomId INTEGER NOT NULL,
CalcDir TEXT NOT NULL);
CREATE TABLE Exports(
Id INTEGER PRIMARY KEY,
CalcId INTEGER NOT NULL,
NumCalc INTEGER DEFAULT 0,
Status INTEGER DEFAULT 0,
ExpDT DATETIME,
ImpDT DATETIME,
ExpGeomIds TEXT);
END TRANSACTION;
"""


sql_nbrtable_commands = """
BEGIN TRANSACTION;
CREATE TABLE NbrTable (GeomId INTEGER, NbrId INTEGER, Depth INTEGER, Dist REAL);
END TRANSACTION;
"""



# a simple distance of atwo points on 2D
# @jit('float64(float64[:,:], float64[:,:])')
# def distance(xy1, xy2):
#     return np.sqrt((xy1[0] - xy2[0])**2 + (xy1[1] - xy2[1])**2)


# calculate RMSD distance after kabsch rotation
# @jit('float64(float64[:,:], float64[:,:])',cache=True,fastmath=True,nopython=True)
def kabsch_rmsd(p,q):
    c = np.dot(np.transpose(p), q)                   # covariance matrix
    v, _, w = np.linalg.svd(c)                       # rotaion matrix using singular value decomposition
    if (np.linalg.det(v) * np.linalg.det(w)) < 0.0 : # proper sign of matrix for right-handed coordinate system
        w[-1] = -w[-1]
    r= np.dot(v, w)                                  # kabsch rotation matrix
    p = np.dot(p, r)
    return np.sqrt(np.sum((p-q)**2)/p.shape[0])


try: # JIT compile the above function to speed up using numba
    from numba import jit
    kabsch_rmsd = jit('float64(float64[:,:], float64[:,:])',fastmath=True,nopython=True)(kabsch_rmsd)
except:
    print('Numba not available. Use numba to run the code faster.')

# return cartesian corordinate with their centroid transalted to origin
def centroid(geom):
    p = geomObj.getCart(*geom[1:])
    return p-np.mean(p, axis=0)


r50 = np.deg2rad(50)
lim = 30


# Calculate list of geometries in ascending order of their RMSD from the `geom`
def getKabsch(geom):
    #accessing the full geomList and cartesians from the global scope
    # WARNING !!! Do not use this approach with multiprocessing in windows systems
    vGeomIndex =np.where(                               # return indexes where the geometries satisfies the condition
                    (geomList[:,1]  >= geom[1]-4.5) &
                    (geomList[:,1]  <= geom[1]+4.5) &
                    # (geomList[:,2]  >= geom[2]-r50) &
                    # (geomList[:,2]  >= geom[2]-r50) &
                    (geomList[:,3]  >= geom[3]-r50) &
                    (geomList[:,3]  <= geom[3]+r50) &
                    (geomList[:, 0] != geom[0])
                    )[0]
    # get the index of current geometries, geomids are sorted (?)
    geomIndex = np.searchsorted(geomList[:, 0], geom[0])
    
    # now calculate the rmsd
    lkabsch = np.array([kabsch_rmsd(cart[geomIndex], cart[i]) for i in vGeomIndex])
    index = lkabsch.argsort()[:lim] # get sorted index of first `lim` element
    # return current geomid, geomid of nearest neighbour and their distances
    return geom[0],geomList[vGeomIndex][index,0].astype(np.int64), lkabsch[index]






# WARNING!!! Do not pollute the module level namespace while using multiprocessing module
if __name__ == "__main__":
    # read database names from (hardcoded here) `pesman.config`
    scf = SafeConfigParser()
    scf.read('pesman.config')
    dbFile = scf.get('DataBase', 'db')
    # nbrdb only to store distances, not going to be used in any calculations
    nbrDbFile = scf.get('DataBase', 'nbr')
    dbExist = os.path.exists(dbFile)

    if dbExist:                    # remove old db if you want or comment it off if want to append to existing database
        os.remove(dbFile)
        dbExist = False
    if os.path.exists(nbrDbFile):  # mandatorily remove nbr db
        os.remove(nbrDbFile)


    with sqlite3.connect(dbFile) as con, sqlite3.connect(nbrDbFile) as conNbr:
        if not dbExist:
            cur = con.cursor()
            cur.executescript(sql_script)

        curNbr = conNbr.cursor()
        curNbr.executescript(sql_nbrtable_commands)

        rho = np.concatenate((np.linspace(2,4.5,6), np.linspace(5,9,17), np.linspace(9,14,11)))
        theta = 3.0
        phi = np.linspace(0,180,61)


        # create the geometry list here
        newGeomList =np.stack( np.meshgrid(rho,theta,phi,indexing='ij'), axis=3).reshape(-1,3)
        newGeomList[:,1:] = np.deg2rad(newGeomList[:,1:])
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
        # create any tags if necessary
        tags = np.apply_along_axis(geomObj.geom_tags, 1, newGeomList)
        newGeomList = np.column_stack([newGeomList, tags])
        # # insert the geometries and tags into database
        cur.executemany('INSERT INTO Geometry (rho,theta,phi,Tags) VALUES (?, ?, ?, ? )', newGeomList)

        #get the updated table with ids
        cur.execute('select id,rho,theta,phi from geometry')
        geomList= np.array(cur.fetchall())

        # Create the cartesian geometries, with centroid translated to origin
        cart = np.apply_along_axis(centroid, 1 , geomList)
        # # Create a pool of workers on all processors of system and feed all the functions (synchronously ???)
        pool = Pool()
        dat = pool.map(getKabsch, geomList)
        for (gId, indexes, distances) in dat:

            cur.execute('UPDATE Geometry SET Nbr = ? where Id=?', (' '.join(map(str,indexes)), gId))
            curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)", [(gId, indexes[i], i, distances[i]) for i in range(lim)])

        # save the geomlist in a datafile
        geomList[:,2:] = np.rad2deg(geomList[:,2:])
        np.savetxt("geomdata.txt", geomList, fmt=['%d', '%.8f', '%.8f', '%.8f'], delimiter='\t')
