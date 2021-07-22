import os,re,sys
import numpy as np
from sqlite3 import connect as sqlConnect
from PESMan import parseConfig
from ImpExp import parseResult



# list of export.dat files are provided through the default command line arguments
# if no argument is provided then only result is saved from the data base
# Run this as `python <this_filename> <list of export.dat files>


config = parseConfig()
dB = config['DataBase']['db']
trim = 4



with sqlConnect(dB) as con:
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
        calcId    = re.findall(r'Export\d+-\w+(\d+)',exportDir)[0]
        cur.execute("SELECT GeomId,CalcDir FROM ExpCalc where ExpId=?",(exportId,))

        for geomId, calcDir in cur.fetchall():
            calcFile= "{0}/{1}/{1}.calc_".format(exportDir, calcDir) # calcfile name
            resFile= "{0}/{1}/{1}.res".format(exportDir, calcDir) # res name

            # if not os.path.isfile(calcFile): # not a failed job
            #     continue
            # if not os.path.isfile(resFile): # `res` file does not exists, nothing to do here
            #     continue
            if not (os.path.isfile(calcFile) and os.path.isfile(resFile)): continue

            # with open(calcFile,'r') as f:
            #     for i in f:
            #         if i.strip().startswith('CalcId'):
            #             calcId = int(i.split(':')[1])
            #             break
            #     else: # no clacid found, never should have happened
            #         assert False, "Bad calc file."

            # check if that geomid and calcid already exist in the database table
            cur.execute('select count(*) FROM SemiCalc where GeomId=? and CalcId=?;',(geomId,calcId))
            counts = cur.fetchone()[0]
            if(counts==0): # no such information so can be added to the database otherwise just continue

                res = parseResult(resFile)
                result.append([ geomId, calcId, res ])

    # add the result into database
    cur.executemany("INSERT INTO SemiCalc (GeomId,CalcId,Results) VALUES (?, ?, ?)", result)
    print('Number of new results added to database {}\n'.format(len(result)))


    # now save the result in a datafile, query result from two tables, check the calc id
    cur.execute("SELECT geomid,results from Calc where CalcId=? union SELECT geomid,results from SemiCalc where CalcId=?",(2,2))
    CalcRow = [[i]+j.split()[:trim] for i,j in cur]  # number 3 has to decided <-- 3 mrci energy
    print('Result collected from database {}\n'.format(len(CalcRow)))
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