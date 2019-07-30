# The schema for format of new data base for main data base is as follows
import os
import time
import sqlite3
import numpy as np
from multiprocessing import Pool



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



def distance(xy1, xy2):
    x1,y1 = xy1 
    x2,y2 = xy2
    return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def getKabsch(geom, lim=10):
    #accessing the full geomList from the global scope
    # WARNING !!! Do not use this approach in windows system, windows doesn't uses fork to spawn child processes
    vGeom = geomList[np.where( 
                    (geomList[:,1] > geom[1]-2.5) &
                    (geomList[:,1] < geom[1]+2.5) &
                    (geomList[:,2] > geom[2]-np.deg2rad(30))  &
                    (geomList[:,2] < geom[2]+np.deg2rad(30))  &
                    (geomList[:, 0] != geom[0])
                    )]
    x, y = geom[3],geom[4]
    lkabsh = np.array([distance(geom[3:], i[3:])  for i in vGeom])
    index = lkabsh.argsort()[:lim]
    txt = ' '.join([str(int(i)) for i in vGeom[index,0]])
    return (txt, geom[0])



# WARNING!!! Do not remove this while using multiprocessing module
if __name__ == "__main__":
    import time
    start = time.time()
    dbfile = "no2db.db"
    con = sqlite3.connect(dbfile)
    try:
        with con:
            cur = con.cursor()
            cur.executescript(sql_script) 

            newGeomList = np.dstack(np.mgrid[0.1:5.0:50j,0:180:181j]).reshape(-1,2)
            newGeomList = np.vstack([[0,0], newGeomList])
            newGeomList[:,1] = np.deg2rad(newGeomList[:,1])

            assert newGeomList.size, "No new geometries to add"
            # create the tags
            # tags = np.apply_along_axis(geomObj.geom_tags, 1, newGeomList)
            # # insert the geometries and tags into database
            cur.executemany('INSERT INTO Geometry (rho,phi) VALUES (?, ? )', newGeomList)

            #get the updated table
            cur.execute('select id,rho,phi from geometry')
            geomList= np.array(cur.fetchall())

            # Create a pool of workers on all processors of system and feed all the functions (synchronously ???)
            x = geomList[:,1]*np.cos(geomList[:,2])
            y = geomList[:,1]*np.sin(geomList[:,2])
            geomList = np.column_stack([geomList, x, y])
            pool = Pool()
            dat = pool.map(getKabsch, geomList)
            cur.executemany('UPDATE Geometry SET Nbr = ? where Id=?', dat)
            geomList[:,2] = np.rad2deg(geomList[:,2])
            np.savetxt("geomdata.txt", geomList[:,:3], fmt=['%d', '%.8f', '%.8f'], delimiter='\t')
    except Exception as e:
        print("Something went wrong. %s"%e)
    finally :
        con.close()
