import sqlite3 
import numpy as np 
from geometry import geomObj


with sqlite3.connect('no2db.db') as con:
    cur = con.cursor()
    cur.execute("SELECT geomid,results from Calc where CalcId=2") 
    CalcRow = [[i[0]]+i[1].split() for i in cur.fetchall()]
    CalcRow = np.array(CalcRow, dtype=np.float64)

    cur.execute("SELECT id,rho,phi from Geometry ")
    GeomRow = np.array(cur.fetchall())

# This is the list of indexes in geomrow corresponding to the id in calcrow
sortedIndex = np.searchsorted(GeomRow[:,0], CalcRow[:,0], sorter=GeomRow[:,0].argsort())
resArr = np.column_stack([ GeomRow[sortedIndex][:,1:], CalcRow[:,1:]]) # array of [[rho, phi, results..]...]
# sort out jumbling of rho, phi values, also remove any duplicates in process
# not necessary if data is sorted and without duplicates
resArr = np.unique(resArr, axis=0)


aq = geomObj.wfm

# gradRes in shape of (rows, ireps, atoms, coord)
gradRes = resArr[:,2:].reshape(-1,2,3,3)
rhoPhi  = resArr[:,:2]

# Total tau, square and element wise sum of the innermost two axis
tau = np.einsum('ijkl,ijkl->ij', gradRes, gradRes)
tau = np.column_stack([rhoPhi, np.sqrt(tau)])

#elementwise sum of innermost two axis , keeping frquency axis free
tauq = np.abs(np.einsum('ijkl,klm->ijm',gradRes, aq))
# remember the last index was the normal mode axis
tauQ1 = np.column_stack([rhoPhi, tauq[...,0]])
tauQ2 = np.column_stack([rhoPhi, tauq[...,1]])


mult = np.apply_along_axis(lambda x : np.array([[np.cos(x[1]), np.sin(x[1])], [-x[0]*np.sin(x[1]), x[0]*np.cos(x[1])]]), 1, rhoPhi )
trph =  np.abs(np.einsum('nsij,ijk,nlk->nsl', gradRes, aq, mult))


tauRho = np.column_stack([rhoPhi, trph[...,0]])
tauPhi = np.column_stack([rhoPhi, trph[...,1]])


tauFile    = open('Result_files_Nact/TAU/Tau.dat','wb')
tauQ1File  = open('Result_files_Nact/TAU-Q1/TauQ1.dat','wb')
tauQ2File  = open('Result_files_Nact/TAU-Q2/TauQ2.dat','wb')
tauRhoFile = open('Result_files_Nact/TAU-RHO/TauRho.dat','wb')
tauPhiFile = open('Result_files_Nact/TAU-PHI/TauPhi.dat','wb')

rhoList = np.unique(rhoPhi[:,0])
for rho in rhoList:
    ind = np.where(rhoPhi[:,0]==rho)
    
    np.savetxt( tauFile, tau[ind] ,delimiter="\t", fmt=str("%.7f"))
    np.savetxt( tauQ1File, tauQ1[ind] ,delimiter="\t", fmt=str("%.7f"))
    np.savetxt( tauQ2File, tauQ2[ind] ,delimiter="\t", fmt=str("%.7f"))
    np.savetxt( tauRhoFile, tauRho[ind] ,delimiter="\t", fmt=str("%.7f"))
    np.savetxt( tauPhiFile, tauPhi[ind] ,delimiter="\t", fmt=str("%.7f"))

    tauFile.write('\n')
    tauQ1File.write('\n')
    tauQ2File.write('\n')
    tauRhoFile.write('\n')
    tauPhiFile.write('\n')


# an TAU-THETA NACT func for scattering system, provided resArr has rho,theta,phi, grads...
# dth = np.deg2rad(0.03)
# def getTauTheta(geomDat):
#     # now geomdat has values rho,theta,phi,grad1,.......
#     rho,theta,phi = geomDat[:3]
#     grads = geomDat[3:].reshape(3,3)
#     mainCart = geomObj.getCart(rho, theta, phi)
#     # now calculate the dx/dtheta

#     thePlCart = geomObj.getCart(rho, theta+dth, phi)
#     theMnCart = geomObj.getCart(rho, theta-dth, phi)
#     gradTheta = (thePlCart-theMnCart)/(2.0*dth)
#     tauTh = np.abs(np.einsum('ij,ij',grads,gradTheta))
#     return np.array([rho,theta, phi,tauTh])

# result = np.apply_along_axis(getTauTheta, 1, resArr)

# file = open('TAU-THETA.dat','wb')
# for rho in np.unique(result[:,0]):
#     np.savetxt( file, result[result[:,0]==rho] ,delimiter="\t", fmt=str("%.10f"))
#     file.write('\n')