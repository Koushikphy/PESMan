import os,re,sqlite3,sys
import numpy as np 
from ConfigParser import SafeConfigParser
from ImpExp import parseResult



# list of export.dat files are provided through the default command line arguments
# if no argument is provided then only result is saved from the data base
# Run this as `python <this_filename> <list of export.dat files>


scf = SafeConfigParser()
scf.read('pesman.config')
dB = scf.get('DataBase', 'db')


with sqlite3.connect(dB) as con:
    cur = con.cursor()
    # create a new table that will hold the semi successful jobs, no other information is required at this moment
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS SemiCalc(
    GeomId INTEGER NOT NULL,
    CalcId INTEGER NOT NULL,
    Results TEXT);
    ''')

    result = []
    for expFile in sys.argv[1:]: # multiple expdirs is allowed through list input

        exportDir = os.path.abspath(os.path.dirname(expFile))   # get the main export directory
        exportId  = re.findall(r'Export(\d+)-', exportDir)[0]     # get the export id, from the directroy name
    
        cur.execute("SELECT GeomId,CalcDir FROM ExpCalc where ExpId=?",(exportId,))

        for geomId, calcDir in cur.fetchall():
            calcFile= "{0}/{1}/{1}.calc_".format(exportDir, calcDir) # calcfile name
            resFile= "{0}/{1}/{1}.res".format(exportDir, calcDir) # calcfile name
            with open(calcFile,'r') as f:
                for i in f:
                    if i.strip().startswith('CalcId'):
                        calcId = int(i.split(':')[1])
                        break
            if(os.path.isfile(calcFile) and os.path.isfile(resFile)):
                res = parseResult(resFile)
            # check if that geomid and calcid already exist in the database table
            else:
                continue
            
            cur.execute('select count(*) FROM SemiCalc where GeomId=? and CalcId=?;',(geomId,calcId))
            counts = cur.fetchone()[0]
            if(counts==0): # no such information so can be added to the database
                result.append([ geomId, calcId, res ])

    print('Number of new results added to database {}'.format(len(result)))
    cur.executemany("INSERT INTO SemiCalc (GeomId,CalcId,Results) VALUES (?, ?, ?)", result)



# now save the result in a datafile ================================================
    # query result from two tables
    cur.execute("SELECT geomid,results from Calc where CalcId=? union SELECT geomid,results from SemiCalc where CalcId=?",(2,2))
    CalcRow = [[i]+j.split()[:3] for i,j in cur]  # number 3 has to decided <-- 3 mrci energy
    try:
        CalcRow = np.array(CalcRow, dtype=np.float64)
    except:# somthing wrong with the res files
        ind = len(CalcRow[0])
        for i in CalcRow:
            if ind!=len(i):
                raise Exception("Some thing wrong with the result of GeomID %s"%i[0])

    cur.execute("SELECT id,rho,theta,phi from Geometry")
    GeomRow = np.array(cur.fetchall())

    sortedIndex = np.searchsorted(GeomRow[:,0], CalcRow[:,0], sorter=GeomRow[:,0].argsort())
    resArr = np.column_stack([ GeomRow[sortedIndex][:,1:], CalcRow[:,1:]])
    resArr = np.unique(resArr, axis=0)

    resArr[:,[1,2]] = np.rint(np.rad2deg(resArr[:,[1,2]]))        # Caution about the rint
    resArr[:,3:] += 1.67381329                                    # scale energy

    # remove energy above phi 120, as you are going to repeat that anyway
    resArr = resArr[resArr[:,2]<=120]

    with open('Results/Enr_Mrci_extra.dat','w') as f:
        for t in np.unique(resArr[:,1]):
            np.savetxt(f,resArr[resArr[:,1]==t],delimiter='\t',fmt='%.8f')
            f.write('\n')

    print('Result saved as Results/Enr_Mrci_extra.dat')