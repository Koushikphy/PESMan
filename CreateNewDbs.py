import os
import sys
import sqlite3
import numpy as np
from geometry import geomObj
from multiprocessing import Pool
# works both with python 2 and 3
if sys.version_info.major>2:
    from configparser import ConfigParser as ConfigParser
else :
    from ConfigParser import SafeConfigParser as ConfigParser

sql_script = """
BEGIN TRANSACTION;
CREATE TABLE Geometry(
Id INTEGER PRIMARY KEY,
$$
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



# a simple distance of atwo points on 2D, used in spectroscopic case
#@jit('float64(float64[:,:], float64[:,:])')
def distance(geom1, geom2):
    _,rho1,phi1 = geom1
    _,rho2,phi2 = geom2
    xy1 = [rho1*np.cos(phi1), rho1*np.sin(phi1)]
    xy2 = [rho2*np.cos(phi2), rho2*np.sin(phi2)]
    return np.sqrt((xy1[0] - xy2[0])**2 + (xy1[1] - xy2[1])**2)



# return cartesian corordinate with their centroid transalted to origin
def centroid(geom):
    p = geomObj.getCart(*geom[1:])
    return p-np.mean(p, axis=0)


# calculate RMSD distance after kabsch rotation
#@jit('float64(float64[:,:], float64[:,:])',fastmath=True,nopython=True)
def kabsch_rmsd(p,q):
    c = np.dot(np.transpose(p), q)                   # covariance matrix
    v, _, w = np.linalg.svd(c)                       # rotaion matrix using singular value decomposition
    if (np.linalg.det(v) * np.linalg.det(w)) < 0.0 : # proper sign of matrix for right-handed coordinate system
        w[-1] = -w[-1]
    r= np.dot(v, w)                                  # kabsch rotation matrix
    p = np.dot(p, r)
    return np.sqrt(np.sum((p-q)**2)/p.shape[0])

try:
    from numba import jit
    kabsch_rmsd = jit('float64(float64[:,:], float64[:,:])',fastmath=True,nopython=True)(kabsch_rmsd)
    distance = jit('float64(float64[:], float64[:])',fastmath=True,nopython=True)(distance)
except:
    print('Numba JIT compilation not available. Use numba to run the code faster.')



# Calculate list of geometries in ascending order of their RMSD from the `geom`
def getKabsch(geom):
    #accessing the full geomList and cartesians from the global scope
    # WARNING !!! Do not use this approach with multiprocessing in windows systems
    vGeomIndex =np.where(                               # return indexes where the geometries satisfies the condition
                    # (geomList[:,1]  >= geom[1]-ranges[0]) &   # commenting rho range check for hyper
                    # (geomList[:,1]  <= geom[1]+ranges[0]) &
                    (geomList[:,2]  >= geom[2]-ranges[1]) &
                    (geomList[:,2]  <= geom[2]+ranges[1]) &
                    (geomList[:,3]  >= geom[3]-ranges[2]) &
                    (geomList[:,3]  <= geom[3]+ranges[2]) &
                    (geomList[:, 0] != geom[0])
                    )[0]
    # get the index of current geometries, provided geomids are sorted (?)
    geomIndex = np.searchsorted(geomList[:, 0], geom[0])
    # now calculate the rmsd
    lkabsch = np.array([kabsch_rmsd(cart[geomIndex], cart[i]) for i in vGeomIndex])
    index = lkabsch.argsort()[:lim] # get sorted index of first `lim` element
    # return current geomid, geomid of nearest neighbour and their distances
    return geom[0],geomList[vGeomIndex][index,0].astype(np.int64), lkabsch[index]


# Calculate list of geometries in ascending order of their RMSD from the `geom`, only for spec
def getKabsch_norm(geom):
    #accessing the full geomList and cartesians from the global scope
    # WARNING !!! Do not use this approach with multiprocessing in windows systems
    vGeomIndex =np.where(                               # return indexes where the geometries satisfies the condition
                    (geomList[:,1]  >= geom[1]-ranges[0]) &
                    (geomList[:,1]  <= geom[1]+ranges[0]) &
                    (geomList[:,2]  >= geom[2]-ranges[1]) &
                    (geomList[:,2]  <= geom[2]+ranges[1]) &
                    (geomList[:, 0] != geom[0])
                    )[0]
    # get the index of current geometries, provided geomids are sorted (?)
    geomIndex = np.searchsorted(geomList[:, 0], geom[0])
    lkabsch = np.array([distance(geomList[geomIndex], geomList[i]) for i in vGeomIndex])
    index = lkabsch.argsort()[:lim] # get sorted index of first `lim` element
    # return current geomid, geomid of nearest neighbour and their distances
    return geom[0],geomList[vGeomIndex][index,0].astype(np.int64), lkabsch[index]






# WARNING!!! Do not pollute the module level namespace while using multiprocessing module
if __name__ == "__main__":

    scf = ConfigParser()
    scf.read('pesman.config')
    dbFile = scf.get('DataBase', 'db')
    # nbrdb only to store distances, not going to be used in any calculations
    nbrDbFile = scf.get('DataBase', 'nbr')
    dbExist = os.path.exists(dbFile)
    # neighbour limit to search for 
    lim = 30

    # #%%%%%%%%%%%%%%%%%%%%%%%%%% for scattering hyperspherical %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    sql_script = sql_script.replace('$$', 'rho REAL,\ntheta REAL,\nphi REAL,')
    rho = 2.5
    ranges = [4.5,np.deg2rad(30),np.deg2rad(30)]

    # if dbExist:                    # remove old db if you want or comment it off if want to append to existing database
        # os.remove(dbFile)
        # dbExist = False
    if os.path.exists(nbrDbFile):  # mandatorily remove nbr db
        os.remove(nbrDbFile)


    with sqlite3.connect(dbFile) as con, sqlite3.connect(nbrDbFile) as conNbr:
        cur = con.cursor()
        if not dbExist: cur.executescript(sql_script)

        curNbr = conNbr.cursor()
        curNbr.executescript(sql_nbrtable_commands)

        # create the geometry list here
        # newGeomList =np.stack( np.mgrid[rho:rho:1j, 0:90:46j, 0:180:61j], axis=3).reshape(-1,3)
        
        newGeomList = np.vstack([
                 [rho,0,0],
                 np.stack( np.mgrid[rho:rho:1j, 2:50:25j, 0:180:181j], axis=3).reshape(-1,3),
                 np.stack( np.mgrid[rho:rho:1j, 51:90:40j, 0:180:181j], axis=3).reshape(-1,3)
        ])


        newGeomList[:,1:] = np.deg2rad(newGeomList[:,1:])
        # if db exists then check if any duplicate geometry is being passed, if yes, then remove it

        if dbExist:
            cur.execute('select rho,theta,phi from geometry')
            oldTable = [list(i) for i in cur.fetchall()] # sqlite returns tuple and python being strongly typed, they have to manually cast
            if len(oldTable):
                dupInd = np.array([i in oldTable for i in newGeomList.tolist()]) # weired, direct numpy approach not working properly
                dSize = dupInd[dupInd==True].shape[0]
                uSize = dupInd[dupInd==False].shape[0]
                if uSize:
                    print("{} geometries already exist in the old database, {} additional geometries will be added".format(dSize, uSize))
                    newGeomList = newGeomList[~dupInd]


        assert newGeomList.size, "No new geometries to add"
        # create any tags if necessary

        tags = np.array([geomObj.geom_tags(i) for i in newGeomList])  
        newGeomList = np.column_stack([newGeomList, tags])
        # # insert the geometries and tags into database
        cur.executemany('INSERT INTO Geometry (rho,theta,phi,Tags) VALUES (?, ?, ?, ? )', newGeomList)

        #get the updated table with ids
        cur.execute('select id,rho,theta,phi from geometry')
        geomList= np.array(cur.fetchall())

        # # Create the cartesian geometries, with centroid translated to origin
        cart = np.array([centroid(i) for i in geomList ])
        # # Create a pool of workers on all processors of system and feed all the functions (synchronously ???)
        pool = Pool()
        dat = pool.map(getKabsch, geomList)
        for (gId, indexes, distances) in dat:

            cur.execute('UPDATE Geometry SET Nbr = ? where Id=?', (' '.join(map(str,indexes)), gId))
            # curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)", [(gId, indexes[i], i, distances[i]) for i in range(lim)])
            curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)", [(gId, ind, i, dis) for i, (ind,dis) in enumerate(zip(indexes, distances))] )
        # # save the geomlist in a datafile
        geomList[:,2:] = np.rad2deg(geomList[:,2:])
        np.savetxt("geomdata.txt", geomList, fmt=['%d', '%.8f', '%.8f', '%.8f'], delimiter='\t')

    print('Database {} created'.format(dbFile))

    # #%%%%%%%%%%%%%%%%%%%%%%%%%% for scattering jacobi system %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%5
    # sql_script = sql_script.replace('$$', 'sr REAL,\ncr REAL,\ngamma REAL,')
    # ranges = [4.5,4.5,np.deg2rad(30)]

    # if dbExist:                    # remove old db if you want or comment it off if want to append to existing database
    #     os.remove(dbFile)
    #     dbExist = False
    # if os.path.exists(nbrDbFile):  # mandatorily remove nbr db
    #     os.remove(nbrDbFile)


    # with sqlite3.connect(dbFile) as con, sqlite3.connect(nbrDbFile) as conNbr:
    #     if not dbExist:
    #         cur = con.cursor()
    #         cur.executescript(sql_script)

    #     curNbr = conNbr.cursor()
    #     curNbr.executescript(sql_nbrtable_commands)

    #     # create the geometry list here
    #     newGeomList =np.stack( np.mgrid[2.0:2.0:1j, 0:10:101j, 0:90:19j], axis=3).reshape(-1,3)
    #     newGeomList[:,2] = np.deg2rad(newGeomList[:,2])
    #     # if db exists then check if any duplicate geometry is being passed, if yes, then remove it
    #     # if dbExist: 
    #     #     cur.execute('select rho,phi from geometry')
    #     #     oldTable = np.array(cur.fetchall())
    #     #     if oldTable.size:
    #     #         dupInd = np.any(np.isin( oldTable, newGeomList), axis=1)
    #     #         if dupInd.size:
    #     #             print("%s duplicates found in new list of geometries"%dupInd.size)
    #     #             newGeomList = np.delete(newGeomList, np.where(dupInd), axis=0) # delete duplicates



    #     assert newGeomList.size, "No new geometries to add"
    #     # create any tags if necessary
    #     tags = np.apply_along_axis(geomObj.geom_tags, 1, newGeomList)
    #     newGeomList = np.column_stack([newGeomList, tags])
    #     # # insert the geometries and tags into database
    #     cur.executemany('INSERT INTO Geometry (sr,cr,gamma,Tags) VALUES (?, ?, ?, ? )', newGeomList)

    #     #get the updated table with ids
    #     cur.execute('select id,sr,cr,gamma from geometry')
    #     geomList= np.array(cur.fetchall())

    #     # Create the cartesian geometries, with centroid translated to origin
    #     cart = np.apply_along_axis(centroid, 1 , geomList)
    #     # # Create a pool of workers on all processors of system and feed all the functions (synchronously ???)
    #     pool = Pool()
    #     dat = pool.map(getKabsch, geomList)
    #     for (gId, indexes, distances) in dat:

    #         cur.execute('UPDATE Geometry SET Nbr = ? where Id=?', (' '.join(map(str,indexes)), gId))
    #         curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)", [(gId, indexes[i], i, distances[i]) for i in range(lim)])

    #     # save the geomlist in a datafile
    #     geomList[:,3] = np.rad2deg(geomList[:,3])
    #     np.savetxt("geomdata.txt", geomList, fmt=['%d', '%.8f', '%.8f', '%.8f'], delimiter='\t')



    #%%%%%%%%%%%%%%%%%%%%%%%%%% for spectroscopic normal mode %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # sql_script = sql_script.replace('$$', 'rho REAL,\nphi REAL,')
    # ranges = [4.5,np.deg2rad(30)]

    # if dbExist:                    # remove old db if you want or comment it off if want to append to existing database
    #     os.remove(dbFile)
    #     dbExist = False
    # if os.path.exists(nbrDbFile):  # mandatorily remove nbr db
    #     os.remove(nbrDbFile)


    # with sqlite3.connect(dbFile) as con, sqlite3.connect(nbrDbFile) as conNbr:
    #     if not dbExist:
    #         cur = con.cursor()
    #         cur.executescript(sql_script)

    #     curNbr = conNbr.cursor()
    #     curNbr.executescript(sql_nbrtable_commands)

    #     # create the geometry list here
    #     newGeomList =np.stack( np.mgrid[0.1:5.0:50j,0:180:181j], axis=2).reshape(-1,2)
    #     newGeomList[:,1] = np.deg2rad(newGeomList[:,1])
    #     # if db exists then check if any duplicate geometry is being passed, if yes, then remove it
    #     # if dbExist: 
    #     #     cur.execute('select rho,phi from geometry')
    #     #     oldTable = np.array(cur.fetchall())
    #     #     if oldTable.size:
    #     #         dupInd = np.any(np.isin( oldTable, newGeomList), axis=1)
    #     #         if dupInd.size:
    #     #             print("%s duplicates found in new list of geometries"%dupInd.size)
    #     #             newGeomList = np.delete(newGeomList, np.where(dupInd), axis=0) # delete duplicates



    #     # assert newGeomList.size, "No new geometries to add"
    #     # create any tags if necessary
    #     # tags = np.apply_along_axis(geomObj.geom_tags, 1, newGeomList)
    #     # newGeomList = np.column_stack([newGeomList, tags])
    #     # # insert the geometries and tags into database
    #     cur.executemany('INSERT INTO Geometry (rho,phi) VALUES (?, ?)', newGeomList)

    #     #get the updated table with ids
    #     cur.execute('select id,rho,phi from geometry')
    #     geomList= np.array(cur.fetchall())

    #     # # Create a pool of workers on all processors of system and feed all the functions (synchronously ???)
    #     pool = Pool()
    #     dat = pool.map(getKabsch_norm, geomList)
    #     for (gId, indexes, distances) in dat:
    #         cur.execute('UPDATE Geometry SET Nbr = ? where Id=?', (' '.join(map(str,indexes)), gId))
    #         curNbr.executemany("INSERT INTO NbrTable VALUES (?,?,?,?)", [(gId, indexes[i], i, distances[i]) for i in range(lim)])

    #     # save the geomlist in a datafile
    #     geomList[:,2] = np.rad2deg(geomList[:,2])
    #     np.savetxt("geomdata.txt", geomList, fmt=['%d', '%.8f', '%.8f'], delimiter='\t')