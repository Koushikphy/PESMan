import os 
import numpy as np
from sqlite3 import connect as sqlConnect
from geometry import geomObj
from PESMan import parseConfig



def readDB(db, calcId, cols):
    with sqlConnect(db) as con:
        cur = con.cursor()
        cur.execute("SELECT geomid,results from Calc where CalcId=?",(calcId,))
        CalcRow = [[i]+j.split() for i,j in cur]
        try:
            CalcRow = np.array(CalcRow, dtype=np.float64)
        except:# somthing wrong with the res files
            ind = len(CalcRow[0])
            for i in CalcRow:
                if ind!=len(i):
                    raise Exception("Some thing wrong with the result of GeomID %s"%i[0])

        cur.execute("SELECT id,%s from Geometry"%cols)
        GeomRow = np.array(cur.fetchall())

    # This is the list of indexes in geomrow corresponding to the id in calcrow
    sortedIndex = np.searchsorted(GeomRow[:,0], CalcRow[:,0], sorter=GeomRow[:,0].argsort())
    # each row of resArr  contains [rho, phi, results...]
    resArr = np.column_stack([ GeomRow[sortedIndex][:,1:], CalcRow[:,1:]])
    # sort out jumbling of rho, phi values, also remove any duplicates in process, be careful !!!
    resArr = np.unique(resArr, axis=0)
    return resArr




# def parseEnr(resArr, resDir):
#     # resArr contains geoms and results
#     gRes = open(resDir+'/Enr.dat', "wb")
#     for rho in np.unique(resArr[:,0]):
#         rhoBlock = resArr[resArr[:,0]==rho]
#         saveData(gRes, rhoBlock)
#     gRes.close()



# # analytical NACT for spectroscopic case
# # bohr inverse to angstorm inverse ???
# def parseNACTspecAna(resArr, pairs, atoms):
#     wfm = geomObj.wfm
    
#     # wfm is in shape of (masses, frequencies (i.e 2), coordinates (i.e. 3; x,y,z))
#     # given each result string holdes the gradiend data for all the ireps/pairs
#     # gradRes is in shape of (rows, pairs/ireps, atoms, coord)
#     gradRes = resArr[:,2:].reshape(-1,pairs,atoms,3)
#     rhoPhi  = resArr[:,:2]

#     angtobohr    = 1.8897259886
#     gradRes     *= angtobohr

#     # Total tau, square and element wise sum of the innermost two axis
#     tau = np.einsum('ijkl,ijkl->ij', gradRes, gradRes)
#     tau = np.column_stack([rhoPhi, np.sqrt(tau)])

#     #elementwise sum of innermost two axis , keeping frquency axis free
#     tauq = np.abs(np.einsum('ijkl,klm->ijm',gradRes, wfm))
#     # remember the last index was the normal mode axis
#     tauQ1 = np.column_stack([rhoPhi, tauq[...,0]])
#     tauQ2 = np.column_stack([rhoPhi, tauq[...,1]])

#     mult = np.apply_along_axis(lambda x : np.array(
#            [[np.cos(x[1]), np.sin(x[1])], [-x[0]*np.sin(x[1]), x[0]*np.cos(x[1])]]), 1, rhoPhi )
#     trph =  np.abs(np.einsum('nsij,ijk,nlk->nsl', gradRes, wfm, mult))

#     tauRho = np.column_stack([rhoPhi, trph[...,0]])
#     tauPhi = np.column_stack([rhoPhi, trph[...,1]])

#     # whatever directory name you use, make sure they exists
#     tauFile    = open('Result_files_Nact/TAU/Tau.dat','wb')
#     tauQ1File  = open('Result_files_Nact/TAU-Q1/TauQ1.dat','wb')
#     tauQ2File  = open('Result_files_Nact/TAU-Q2/TauQ2.dat','wb')
#     tauRhoFile = open('Result_files_Nact/TAU-RHO/TauRho.dat','wb')
#     tauPhiFile = open('Result_files_Nact/TAU-PHI/TauPhi.dat','wb')

#     for rho in np.unique(rhoPhi[:,0]):
#         ind = np.where(rhoPhi[:,0]==rho)
#         saveData(tauFile, tau[ind])
#         saveData(tauQ1File, tauQ1[ind])
#         saveData(tauQ2File, tauQ2[ind])
#         saveData(tauRhoFile, tauRho[ind])
#         saveData(tauPhiFile, tauPhi[ind])



# # analytical NACT for scattering case
# def getTauTheta(geomDat):
#     # now geomdat has values rho,theta,phi,grad1,.......
#     dth = np.deg2rad(0.03)
#     rho,theta,phi = geomDat[:3]
#     grads = geomDat[3:].reshape(3,3)
#     # mainCart = geomObj.getCart(rho, theta, phi)
#     # now calculate the dx/dtheta

#     thePlCart = geomObj.getCart(rho, theta+dth, phi)
#     theMnCart = geomObj.getCart(rho, theta-dth, phi)
#     gradTheta = (thePlCart-theMnCart)/(2.0*dth)
#     tauTh = np.abs(np.einsum('ij,ij',grads,gradTheta))
#     return np.array([rho,theta, phi,tauTh])



# def parseNACTscatAna(resArr):
#     result = np.apply_along_axis(getTauTheta, 1, resArr)

#     file = open('TAU-THETA.dat','wb')
#     for rho in np.unique(result[:,0]):
#         saveData(file, result[result[:,0]==rho])




# for H3 purpose
def parseMultiEnr(resArr,resDir):
    thetaList = np.unique(resArr[:,1])
    with open(resDir+'/Enr_Multi.dat','w') as f:
        for theta in thetaList:
            dat = resArr[resArr[:,1]==theta]
            np.savetxt(f,dat,delimiter='\t',fmt='%.8f')
            f.write('\n')


def parseMrciDdrNACT(resArr,resDir):
    assert resArr.shape[1]==18, 'Not enough data in result'

    resArr[:,[1,2]] = np.rint(np.rad2deg(resArr[:,[1,2]]))
    thetaList = np.unique(resArr[:,1])
    mrciData = resArr[:,0:6]
    tautData = np.abs(resArr[:,np.r_[0:3,6:12]])
    taupData = np.abs(resArr[:,np.r_[0:3,12:18]])
    mrciData[:,3:]+=1.67381329  # scale energy
    tautData[:,3:]*=180.0/np.pi # DDR nact conversion from radian to degree
    taupData[:,3:]*=180.0/np.pi

    with open(resDir+'/Enr_Mrci.dat','w') as f, open(resDir+'/TauThetaNACT.dat','w') as g, open(resDir+'/TauPhiNACT.dat','w') as h:
        for theta in thetaList:
            ind = np.where(mrciData[:,1]==theta)
            np.savetxt(f,mrciData[ind],delimiter='\t',fmt='%.8f')
            np.savetxt(g,tautData[ind],delimiter='\t',fmt='%.8f')
            np.savetxt(h,taupData[ind],delimiter='\t',fmt='%.8f')
            f.write('\n')
            g.write('\n')
            h.write('\n')



def parseMultiEnr_Util():
    config = parseConfig()
    dB = config['DataBase']['db']
    resDir = "Results"
    if not os.path.exists(resDir) : os.makedirs(resDir)

    # read the result from database
    resArr = readDB(dB, calcId=1, cols='rho,theta,phi')
    parseMultiEnr(resArr,resDir)



def parseMrciDdrNACT_Util():
    config = parseConfig()
    dB = config['DataBase']['db']
    resDir = "Results"
    if not os.path.exists(resDir) : os.makedirs(resDir)

    resArr = readDB(dB, calcId=2, cols='rho,theta,phi')
    parseMrciDdrNACT(resArr,resDir)
    print("NACT & MRCI Energy data parsed and saved")




if __name__ == "__main__":
    parseMrciDdrNACT_Util()
