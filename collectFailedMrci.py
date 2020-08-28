# For H3 system the mrci energy and the ddr nact is done in the same template. So if the energy is done but the nact is failed
# the whole job is falied and the pesman can't import the job for that particular geometry, even though the enrgy result is available 
# this script searches for such jobs in the run directories and collect them


import os,re,sqlite3
import numpy as np 



# export/rundirs where the jobs are run
expDirs = ['ExpDir/Export1892-mrciddr2']




def parseResult(file):
    # Collects any valid number and returns the result as a string
    with open(file, 'r') as f: txt = f.read()
    txt = txt.replace('D','E')
    res = re.findall(r"(?:(?<=^)|(?<=\s))([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)(?=\s|$|\n|\r\n)", txt)
    return ' '.join(res)


# will totally ignore the nact result if there is something and only catch the energy values 
# now there is some time double enerfy values recorded due to soem trun problem
# so the safe option is to just take the first 3 values


resArr = []
for eD in expDirs:
    with open(eD+"/export.dat") as f: 
        exps = f.read().split("\n",1)[1].split()[1:]

    for i in exps: # search where both "calc_" and "res" is available
        calc = eD+'/{0}/{0}.calc_'.format(i)
        res  = eD+'/{0}/{0}.res'.format(i)
        geomId = re.findall(r'mrciddr2-geom(\d+)',i)
        if(os.path.isfile(calc) and os.path.isfile(res)):
            res = parseResult(res)
            res = res.split()[:3]
            resArr.append(geomId+res)


# now collect the successful energy result and then merge with the before ones to save
with sqlite3.connect('h3.db') as con:
    cur = con.cursor()
    cur.execute("SELECT geomid,results from Calc where CalcId=?",(2,))
    CalcRow = resArr + [[i]+j.split()[:3] for i,j in cur]

    CalcRow = np.array(CalcRow, dtype=np.float64)

    cur.execute("SELECT id,rho,theta,phi from Geometry")
    GeomRow = np.array(cur.fetchall())

sortedIndex = np.searchsorted(GeomRow[:,0], CalcRow[:,0], sorter=GeomRow[:,0].argsort())
resArr = np.column_stack([ GeomRow[sortedIndex][:,1:], CalcRow[:,1:]])
mrciData = np.unique(resArr, axis=0)


thetaList = np.unique(mrciData[:,1])
mrciData[:,[1,2]] = np.rint(np.rad2deg(mrciData[:,[1,2]]))
mrciData[:,3:]+=1.67381329  # scale energy

with open('Results/Enr_Mrci_extra.dat','w') as f:
    for t in np.unique(mrciData[:,1]):
        np.savetxt(f,mrciData[mrciData[:,1]==t],delimiter='\t',fmt='%.8f')
        f.write('\n')