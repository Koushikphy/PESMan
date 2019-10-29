import os 
import sqlite3 
import numpy as np
from geometry import geomObj
from ConfigParser import SafeConfigParser



def saveData(file, data):
    np.savetxt( file, data ,delimiter="\t", fmt="%.8f") 
    file.write('\n')



def readDB(db, calcId, cols):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        cur.execute("SELECT geomid,results from Calc where CalcId=?",(calcId,))
        CalcRow = [[i]+j.split() for i,j in cur]
        CalcRow = np.array(CalcRow, dtype=np.float64)

        cur.execute("SELECT id,%s from Geometry"%cols)
        GeomRow = np.array(cur.fetchall())

    # This is the list of indexes in geomrow corresponding to the id in calcrow
    sortedIndex = np.searchsorted(GeomRow[:,0], CalcRow[:,0], sorter=GeomRow[:,0].argsort())
    # each row of resArr  contains [rho, phi, results...]
    resArr = np.column_stack([ GeomRow[sortedIndex][:,1:], CalcRow[:,1:]])
    # sort out jumbling of rho, phi values, also remove any duplicates in process, be careful !!!
    resArr = np.unique(resArr, axis=0)
    return resArr




def parseEnr(resArr, resDir):
    # resArr contains geoms and results
    gRes = open(resDir+'/Enr.dat', "wb")
    for rho in np.unique(resArr[:,0]):
        rhoBlock = resArr[resArr[:,0]==rho]
        saveData(gRes, rhoBlock)
    gRes.close()



# analytical NACT for spectroscopic case
# bohr inverse to angstorm inverse ???
def parseNACTspecAna(resArr, pairs, atoms):
    wfm = geomObj.wfm
    
    # wfm is in shape of (masses, frequencies (i.e 2), coordinates (i.e. 3; x,y,z))
    # given each result string holdes the gradiend data for all the ireps/pairs
    # gradRes is in shape of (rows, pairs/ireps, atoms, coord)
    gradRes = resArr[:,2:].reshape(-1,pairs,atoms,3)
    rhoPhi  = resArr[:,:2]

    angtobohr    = 1.8897259886
    gradRes     *= angtobohr

    # Total tau, square and element wise sum of the innermost two axis
    tau = np.einsum('ijkl,ijkl->ij', gradRes, gradRes)
    tau = np.column_stack([rhoPhi, np.sqrt(tau)])

    #elementwise sum of innermost two axis , keeping frquency axis free
    tauq = np.abs(np.einsum('ijkl,klm->ijm',gradRes, wfm))
    # remember the last index was the normal mode axis
    tauQ1 = np.column_stack([rhoPhi, tauq[...,0]])
    tauQ2 = np.column_stack([rhoPhi, tauq[...,1]])

    mult = np.apply_along_axis(lambda x : np.array([[np.cos(x[1]), np.sin(x[1])], [-x[0]*np.sin(x[1]), x[0]*np.cos(x[1])]]), 1, rhoPhi )
    trph =  np.abs(np.einsum('nsij,ijk,nlk->nsl', gradRes, wfm, mult))

    tauRho = np.column_stack([rhoPhi, trph[...,0]])
    tauPhi = np.column_stack([rhoPhi, trph[...,1]])

    # whatever directory name you use, make sure they exists
    tauFile    = open('Result_files_Nact/TAU/Tau.dat','wb')
    tauQ1File  = open('Result_files_Nact/TAU-Q1/TauQ1.dat','wb')
    tauQ2File  = open('Result_files_Nact/TAU-Q2/TauQ2.dat','wb')
    tauRhoFile = open('Result_files_Nact/TAU-RHO/TauRho.dat','wb')
    tauPhiFile = open('Result_files_Nact/TAU-PHI/TauPhi.dat','wb')

    for rho in np.unique(rhoPhi[:,0]):
        ind = np.where(rhoPhi[:,0]==rho)
        saveData(tauFile, tau[ind])
        saveData(tauQ1File, tauQ1[ind])
        saveData(tauQ2File, tauQ2[ind])
        saveData(tauRhoFile, tauRho[ind])
        saveData(tauPhiFile, tauPhi[ind])



# analytical NACT for scattering case
def getTauTheta(geomDat):
    # now geomdat has values rho,theta,phi,grad1,.......
    dth = np.deg2rad(0.03)
    rho,theta,phi = geomDat[:3]
    grads = geomDat[3:].reshape(3,3)
    mainCart = geomObj.getCart(rho, theta, phi)
    # now calculate the dx/dtheta

    thePlCart = geomObj.getCart(rho, theta+dth, phi)
    theMnCart = geomObj.getCart(rho, theta-dth, phi)
    gradTheta = (thePlCart-theMnCart)/(2.0*dth)
    tauTh = np.abs(np.einsum('ij,ij',grads,gradTheta))
    return np.array([rho,theta, phi,tauTh])



def parseNACTscatAna(resArr):
    result = np.apply_along_axis(getTauTheta, 1, resArr)

    file = open('TAU-THETA.dat','wb')
    for rho in np.unique(result[:,0]):
        saveData(file, result[result[:,0]==rho])



# modify this function, according to your result and system type
# this function will be called during the RunManger script execution
def main():
    scf = SafeConfigParser()
    scf.read('pesman.config')
    dB = scf.get('DataBase', 'db')

    # read the result from database
    resArr = readDB(dB, calcId=1, cols='rho,theta,phi')

    # now process the result for energy or nact 
    # according to the system type and save them in file
    parseEnr(resArr, resDir='Results_files_Multi')




if __name__ == "__main__":
    main()
