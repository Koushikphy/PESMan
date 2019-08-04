import sqlite3 
import numpy as np 

with sqlite3.connect('no2db.db') as con:
    cur = con.cursor()
    cur.execute("SELECT geomid,results from Calc where CalcId=1")
    CalcRow = [[i[0]]+i[1].split() for i in cur.fetchall()]
    CalcRow = np.array(CalcRow, dtype=np.float64)

    cur.execute("SELECT id,rho,phi from Geometry ")
    GeomRow = np.array(cur.fetchall())

# This is the list of indexes in geomrow corresponding to the id in calcrow
sortedIndex = np.searchsorted(GeomRow[:,0], CalcRow[:,0], sorter=GeomRow[:,0].argsort())
# each row of resArr  contains [rho, phi, results...]
resArr = np.column_stack([ GeomRow[sortedIndex][:,1:], CalcRow[:,1:]])
# sort out jumbling of rho, phi values, also remove any duplicates in process
resArr = np.unique(resArr, axis=0)

ResDir = "Result_files_Multi"
gRes = open(ResDir+'/Enr.dat', "wb")
rhoList = np.unique(resArr[:,0])

for rho in rhoList:
    rhoBlock = resArr[resArr[:,0]==rho]
    sRes = "{}/Enr_rho-{}.dat".format(ResDir, rho)
    np.savetxt( gRes, rhoBlock ,delimiter="\t", fmt=str("%.7f")) #<-- database has upto 7 decimal results
    np.savetxt( sRes, rhoBlock ,delimiter="\t", fmt=str("%.7f")) 
    gRes.write('\n')
gRes.close()