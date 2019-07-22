import sqlite3 
import numpy as np 

with sqlite3.connect('no2db.db') as con:
    cur = con.cursor()
    cur.execute("SELECT geomid,results from Calc where CalcId=2") #<- trick to collect nact jobs
    CalcRow = [[i[0]]+i[1].split() for i in cur.fetchall()]
    CalcRow = np.array(CalcRow, dtype=np.float64)

    cur.execute("SELECT id,rho,phi from Geometry ")
    GeomRow = np.array(cur.fetchall())

# This is the list of indexes in geomrow corresponding to the id in calcrow
sortedIndex = np.searchsorted(GeomRow[:,0], CalcRow[:,0], sorter=GeomRow[:,0].argsort())
resArr = np.column_stack([ GeomRow[sortedIndex][:,1:], CalcRow[:,1:]]) # array of [[rho, phi, results..]...]


hcross    = 0.06350781278
cminvtinv = 0.001883651
ang       = 0.529177249


aq1   = np.loadtxt('./coeff_Q1.dat')
aq2   = np.loadtxt('./coeff_Q3.dat')
aq    = np.column_stack([aq1,aq2]).reshape(3,3,2)
mass  = np.array([14.006700, 15.999400, 15.999400])
msInv  = np.sqrt(1/mass)
omega = np.array([759.61,1687.70 ])
omgInv = np.sqrt(hcross/(omega*cminvtinv))

# innermost axis of aq is the normal modes
aq = np.einsum('ijk,k,i->ijk', aq, omgInv, msInv)/ang


# gradRes in shape of (rows, ireps, atoms, coord)
gradRes = resArr[:,2:].reshape(-1,2,3,3)
rhoPhi  = resArr[:,:2]

# Total tau, square and element wise sum of the innermost two axis
tau = np.einsum('ijkl,ijkl->ij', gradRes, gradRes)
tau = np.column_stack([rhoPhi, np.sqrt(tau)])

#elementwise sum of of innermost two axis , keeping frquency axis free
tauq = np.abs(np.einsum('ijkl,klm->ijm',gradRes, aq))
# remember the last index was the normal mode axis
tauQ1 = np.column_stack([rhoPhi, tauq[...,0]])
tauQ2 = np.column_stack([rhoPhi, tauq[...,1]])

# Can't explain this in just a comment
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