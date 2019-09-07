import sqlite3 
import numpy as np 
from ConfigParser import SafeConfigParser
import os 


def main(db, ResDir):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute("SELECT geomid,results from Calc where CalcId=1")
        CalcRow = [[i[0]]+i[1].split() for i in cur.fetchall()]
        CalcRow = np.array(CalcRow, dtype=np.float64)

        cur.execute("SELECT id,rho,theta,phi from Geometry ")   #<<<<---- change this according to the system
        GeomRow = np.array(cur.fetchall())

    # This is the list of indexes in geomrow corresponding to the id in calcrow
    sortedIndex = np.searchsorted(GeomRow[:,0], CalcRow[:,0], sorter=GeomRow[:,0].argsort())
    # each row of resArr  contains [rho, phi, results...]
    resArr = np.column_stack([ GeomRow[sortedIndex][:,1:], CalcRow[:,1:]])
    # sort out jumbling of rho, phi values, also remove any duplicates in process, be careful !!!
    resArr = np.unique(resArr, axis=0)

    gRes = open(ResDir+'/Enr.dat', "wb")

    for rho in np.unique(resArr[:,0]):
        rhoBlock = resArr[resArr[:,0]==rho]
        # sRes = "{}/Enr_rho-{}.dat".format(ResDir, rho)
        # np.savetxt( sRes, rhoBlock ,delimiter="\t", fmt=str("%.8f")) 
        np.savetxt( gRes, rhoBlock ,delimiter="\t", fmt=str("%.8f")) 
        gRes.write('\n')
    gRes.close()


if __name__ == "__main__":
    ResDir = "Result_files_Multi"      # make sure this directory exists
    if not os.path.exists(ResDir): os.makedirs(ResDir)

    scf = SafeConfigParser()
    scf.read('pesman.config')
    dB = scf.get('DataBase', 'db')
    main(dB, ResDir)
