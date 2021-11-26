from __future__ import print_function
import re
import os
import shutil
from glob import glob
from textwrap import dedent
from multiprocessing import Pool
from tarfile import open as tarOpen
from sqlite3 import connect as sqlConnect, Row as sqlRow
from geometry import geomObj
# initiate the geometry object inside the geometry file and call the methods from there


def parseResult(file):
    # Collects any valid number and returns the result as a string
    with open(file, 'r') as f: txt = f.read()
    txt = txt.replace('D','E')
    res = re.findall(r"(?:(?<=^)|(?<=\s))([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)(?=\s|$|\n|\r\n)", txt)
    return ' '.join(res)


def genCalcFile(CalcId,GeomId,CalcName,Basename,sid,fileName,Desc=""):
    # Creates the calc files
    txt = """# This file is automatically generated. Do not edit.
    CalcId   : {}
    GeomId   : {}
    Name     : {}
    Basename : {}
    StartGId : {}
    Desc     : {}""".format(CalcId,GeomId,CalcName,Basename,sid,Desc)
    with open(fileName, "w") as f:
        f.write(txt)


def ExportJobs(dB, calcId, jobs, np, exportDir, pesDir, templ, gidList, sidList,
                    depth, constDb, includePath, molInfo, par, logger):
    # Main export function that exports a given number of jobs for a specified calcid type
    # following collects the geomid that are exportable and the calc table id which will be used as their start info
    if calcId ==1: # Mrci or nact export
        ExpGeomList = GetExpGeomNearNbr(dB,calcId, gidList, sidList, jobs, depth, constDb, includePath)
    elif calcId==2:
        ExpGeomList = GetExpMrciNactJobs(dB,calcId, jobs, gidList, constDb)
    else:
        raise Exception('No calculation is defined for CalId=',calcId)
        ExpGeomList = successiveExport(dB,calcId, jobs, gidList, constDb)

    with sqlConnect(dB) as con:
        con.row_factory=sqlRow
        cur = con.cursor()

        cur.execute('SELECT * from CalcInfo WHERE Id=?',(calcId,))
        InfoRow = cur.fetchone()
        assert InfoRow, "No Info for CalcId={} found in data base".format(calcId)

        calcName,template = InfoRow['Type'], InfoRow['InpTempl']  # unpack calcname and the template from the info table

        # insert into database one row and use the id as export id
        cur.execute("INSERT INTO Exports (CalcId) VALUES (?)", (calcId,))
        exportId = cur.lastrowid

        expDir = "{}/Export{}-{}{}".format(exportDir, exportId, calcName, calcId)
        # remove the export directory if already exists, may have created from some failed export.
        if os.path.exists(expDir):  shutil.rmtree(expDir) #<<<--- shouldn't have happened
        os.makedirs(expDir)

        if templ:  # if template given use that, o/w use from calcinfo table
            with open(templ,'r') as f: template = f.read()


        jobs = []
        for ind, (geomId,startId) in enumerate(ExpGeomList, start=1):
            cur.execute('SELECT * from Geometry WHERE Id=?',(geomId,))
            geom = dict(cur.fetchone())  # to be parsed in geometry, saving unnecessary

            if startId:
                cur.execute('SELECT GeomId,Dir from Calc WHERE Id=?',(startId,))
                startGId,startDir = cur.fetchone()
            else:
                startGId,startDir = 0, None

            jobs.append([
                geomId, geom, calcId, expDir, template,calcName, startGId, startDir, ind, logger.info if np==1 else print
            ])
        # the logging module though thread safe, can't write from multiple processes, so with multiprocessing simple print is used
        # This situation can be handled properly with an explicit threading queue, but I didn't want to make it all that complicated
        # That means in parallel case the statements inside ExportCalc won't be logged to PESMan.log, only be print to console
        if np==1:
            expDirs = [ExportCalc(i) for i in jobs]
        else: # if parallel export is requested
            pool = Pool(processes=np)
            expDirs = pool.map(ExportCalc,jobs)
            pool.close()


        # update the export table and expcalc tables with the exported jobs
        expGeomIds = [i for i,_ in ExpGeomList]
        cur.execute("UPDATE Exports SET NumCalc=?, ExpDT=strftime('%H:%M:%S %d-%m-%Y', datetime('now', 'localtime')), \
                    ExpGeomIds=? WHERE Id=?", (len(expDirs), ' '.join(map(str,expGeomIds)), exportId))

        lExpCalc = [(exportId,calcId, i,j) for i,j in zip(expGeomIds, expDirs)]
        cur.executemany("INSERT INTO ExpCalc (ExpId,CalcId,GeomId,CalcDir) VALUES (?,?,?,?)",lExpCalc)

        fExportDat = expDir + "/export.dat"                       # save the export id and exported directories in export.dat file
        with open(fExportDat,'w') as f:
            f.write("# Auto generated file. Please do not modify\n"+ ' '.join(map(str,[exportId]+expDirs)))

        os.chmod(fExportDat,0o444)# change mode of this file to read-only to prevent accidental writes

        fPythonFile = "{}/RunJob{}.py".format(expDir, exportId)  # save the python file that will run the jobs

        if par: # export job to run parallel geometry
            createRunJobParallel(molInfo, fPythonFile)
        else: # run a single geometry, mandatory for job like primary mcscf
            createRunJob(molInfo, fPythonFile)  # use only this if you want no parallel geometry

        logger.info("PESMan export successful: Id {} with {} job(s) exported\n".format(exportId, len(ExpGeomList)))
        return expDir, exportId, expDirs




def ExportCalc(arg):  # python 2.7 multiprocessing cant handle argument more than one
    [geomId, geom, calcId, expDir, template, calcName, startGId, startDir, ind, writer] = arg
    writer('Exporting Job No {} with GeomId {}'.format(ind, geomId))

    baseName = "{}{}-geom{}-{}".format(calcName, calcId, geomId, ind)
    exportDir = expDir + "/" + baseName
    os.makedirs(exportDir)

    fCalc = '{}/{}.calc_'.format(exportDir,baseName) # `_` at the end means job not yet done, will be removed after successful run
    fXYZ  = '{}/{}.xyz'.format(exportDir,baseName)
    genCalcFile(calcId,geomId,calcName,baseName,startGId,fCalc)
    geomObj.createXYZfile(geom, fXYZ, ddr=calcId!=1)  #< -- geometry file is created from outside

    if startGId:                       # copy wavefunc if start id is present
        _,a,b = startDir.split("/")     # StartDir -> GeomData/geom1/multi1; StartBaseName -> multi1-geom1
        startBaseName = "{}-{}".format(b,a)
        if os.path.isdir(startDir):   # not in zipped format, copy it to a new name
            shutil.copy("{}/{}.wfu".format(startDir,startBaseName), "{}/{}.wfu".format(exportDir,baseName))
        else:                         # file is in tar
            with tarOpen(startDir+".tar.bz2") as tar:
                tar.extract("./%s.wfu"%startBaseName, path=exportDir) # open tar file and rename it
            os.rename(exportDir+"/%s.wfu"%startBaseName, exportDir+"/%s.wfu"%baseName)

    txt = template.replace("$F$",baseName)
    # generate molpro input file
    fInp = '{}/{}.com'.format(exportDir,baseName)
    with open(fInp,'w') as f: f.write(txt)

    return baseName



def GetExpGeomNearNbr(dB, calcId, gidList, sidList, jobs, maxDepth, constDb, inclPath):
    # Get the exportable geometries and their start id for mulit jobs, returns
    with sqlConnect(dB) as con:
        cur = con.cursor()

        # get jobs that is already done and add to excludegeomlist
        cur.execute("SELECT GeomId,Id FROM Calc WHERE CalcId=?",(calcId,))
        DictCalcId  = dict(cur.fetchall())
        CalcGeomIds = set(DictCalcId.keys())
        ExcludeGeomIds = CalcGeomIds.copy()

        cur.execute("SELECT GeomId FROM ExpCalc WHERE CalcId=?",(calcId,))
        ExcludeGeomIds.update((i for (i,) in cur))

        if gidList:
            sidList += [-1]*(len(gidList)-len(sidList)) # fill sidList if some missing
            DictStartId = dict(zip(gidList, sidList))   # create a dict of start ids

        cond = []
        if gidList:      cond.append( 'id in (' + ",".join(map(str, gidList)) + ')')     #include gidlist
        if constDb:      cond.append( '(' + constDb + ')')                               #include constraint
        if not inclPath: cond.append( "( tags NOT LIKE '%path%' or tags is null)")       #exclude pathological
        # `tags is null` is added as `not like '%path%'` doesn't match `null`!!! Is this the correct way?
        cond = ' where ' + ' and '.join(cond) if cond else ''
        cur.execute('SELECT Id,Nbr FROM Geometry' + cond)


        expGClist = []                                            # list that collects the tuple exportable jobs info
        fullGeomList = []                                         # a naive approach: store all the missed geometries
        for geomId, nbrList in cur:
            if geomId in ExcludeGeomIds: continue                 # geometry already exist, skip
            if gidList and DictStartId[geomId]>=0:                # negetive start id will go to main neighbour searching
                nbrId = DictStartId[geomId]                       # i.e. 0 or positive startid given
                if not nbrId :                                    # 0 startid nothing to do here
                    expGClist.append((geomId, 0))
                elif nbrId in CalcGeomIds :                       # positive start id, include if calculation is already done
                    expGClist.append((geomId, DictCalcId[nbrId]))
                if len(expGClist)==jobs:
                    return expGClist                              # got all the geometries needed
                continue

            nbrList =list(map(int, nbrList.split()))              # Care ful about integer mapping
            nbrId = nbrList[0]                                    # for this initial loop only consider first neighbour

            if nbrId in CalcGeomIds:
                expGClist.append((geomId, DictCalcId[nbrId]))     # got one match
                if len(expGClist)==jobs:
                    return expGClist
                continue
            fullGeomList.append((geomId, nbrList))

        #Get allowed depth. Provided every nbr list has same number of elements. This is be quite bad, do something better
        depth = maxDepth if maxDepth else len(fullGeomList[0][1]) if fullGeomList else 0
        exportedGeom = set([])
        for d in range(1,depth):                                   # depth loop starting from 1 to end,
            for geomId, nbrList in fullGeomList:
                if geomId in exportedGeom: continue

                nbrId = nbrList[d]                                 # get d-th neighbour
                if nbrId in CalcGeomIds:
                    expGClist.append((geomId, DictCalcId[nbrId]))  # got one match now don't search for any other neighbours
                    if len(expGClist)==jobs:
                        return expGClist
                    exportedGeom.add(geomId)

    assert expGClist, "No Exportable geometries found"              # preventing null exports
    return expGClist



def GetExpMrciNactJobs(dB, calcId, jobs, gidList, constDb):

    with sqlConnect(dB) as con:
        cur = con.cursor()
        # #---WARNING:::: turning off constraint, its not that used anyway
        sqlQuery = '''SELECT GeomId,Id FROM Calc 
                    WHERE CalcId = 1 {3} and
                    GeomId not in (SELECT GeomId FROM Calc WHERE CalcId={0} UNION SELECT GeomId FROM ExpCalc WHERE CalcId={0}) 
                    {2} LIMIT {1}'''.format(
                        calcId,
                        jobs, 
                        ' and GeomId in ({})'.format(','.join(map(str,gidList))) if gidList else '',
                        ' and GeomId in ({})'.format(constDb) if constDb else ''
                    )

        cur.execute(sqlQuery)
        expGClist = cur.fetchall()

    assert expGClist, "No Exportable geometries found"            # preventing null exports
    return expGClist


# have to export calcid which is usually more than 2, will export those jobs only that failed in calcid >2
def successiveExport(dB, calcId, jobs, gidList, constDb):
    with sqlConnect(dB) as con:
        cur = con.cursor()

        # get all geoms that is left in the expcalc table for all previous calc ids (greater than 1)
        # if its left in the expcalc (for calcid >1) then it's calcid=1/mcscf was obviously successful.
        sqlQuery = '''SELECT GeomId,Id FROM Calc 
                    WHERE CalcId = 1 and
                    GeomId in (SELECT GeomId from ExpCalc where CalcId={0}) and 
                    GeomId not in (SELECT GeomId FROM Calc WHERE CalcId={1} UNION SELECT GeomId FROM ExpCalc WHERE CalcId={1}) 
                    {3} LIMIT {2}'''.format(
                        calcId-1, calcId,jobs, ' and GeomId in ({})'.format(','.join(map(str,gidList))) if gidList else ''
                    )

        cur.execute(sqlQuery)
        expGClist = cur.fetchall()

    assert expGClist, "No Exportable geometries found"            # preventing null exports
    return expGClist





def ImportJobs(dB, np, expFile, pesDir, iGl, isDel, isZipped, logger):
    # imports jobs from a given export.dat file

    exportDir = os.path.abspath(os.path.dirname(expFile))   # get the main export directory
    exportId  = re.findall(r'Export(\d+)-', exportDir)[0]     # get the export id, from the directroy name
    # so it seems the export.dat is really not needed to import a job, just the path directory is required

    with sqlConnect(dB) as con:
        cur = con.cursor()
        cur.execute('SELECT Status FROM Exports WHERE Id=?',(exportId,))         # check if the export id is open for import
        exp_row = cur.fetchone()
        assert exp_row,        "Export Id = {} not found in data base".format(exportId)
        assert exp_row[0] ==0, "Export Id = {} is already closed.".format(exportId)

        jobs,geomIds = [],[]
        # now obtain list of jobs which can be imported.
        cur.execute("SELECT GeomId,CalcDir FROM ExpCalc where ExpId=?",(exportId,))
        for geomId, calcDir in cur.fetchall():
            dirFull = "{}/{}".format(exportDir,calcDir)             # ab initio directory
            calcFile= "{0}/{1}/{1}.calc".format(exportDir, calcDir) # calcfile name
            if os.path.isfile(calcFile):                            # is this job successful?

                jobs.append([dirFull,calcFile,pesDir,iGl,isZipped,isDel,logger.info if np==1 else print])
                geomIds.append(geomId)

        if np==1:
            res = [ImportCalc(i) for i in jobs]
        else: # if parallel import is requested
            pool = Pool(processes=np)
            res = pool.map(ImportCalc,jobs)
            pool.close()

        cur.executemany("INSERT INTO Calc (GeomId,CalcId,Dir,StartGId,Results) VALUES (?, ?, ?, ?, ?)", res)
        cur.executemany('DELETE FROM ExpCalc WHERE ExpId=? AND GeomId=? ',[(exportId,geomId) for geomId in geomIds])

        cur.execute("UPDATE Exports SET ImpDT=strftime('%H:%M:%S %d-%m-%Y', datetime('now', 'localtime')) WHERE Id=?",(exportId,))

        cur.execute("SELECT count(*) FROM ExpCalc WHERE ExpId=?",(exportId,))
        if cur.fetchone()[0]==0:
            cur.execute("UPDATE Exports SET Status=1 WHERE Id=?",(exportId,))
            logger.info('Export Id={} is now closed.'.format(exportId))
            if isDel:
                logger.info("Deleting export directory {}".format(exportDir))
                shutil.rmtree(exportDir)
        else :
            logger.info('Export Id={} is not closed.'.format(exportId))
        logger.info("{} Job(s) have been successfully imported.\n".format(len(geomIds)))


# WARNING::: `ImportCalc` deletes and moves the files but the database is not updated simultaneously and the same is done 
# at the end to easily use multiprocessing here. usually this doesnot make any  problem, 
# but if the import process carshes at some mid way, then the relevant files will be deleted/moved but no information 
# will be present in the database
#^^^ fix this somehow
#^^^ one solution is to not delete the files. and if reimport needs to be done then it will just replace the files in the GeomData

#NOTE: add an option to check the length of the result data being parsed, and stop if there's something wrong. 
# This will break the above system

def ImportCalc(arg):
    [calcDir,calcFile,pesDir,igList, zipped,isDel,writer] = arg
    writer("Importing {} ...".format(calcDir))
    with open(calcFile,'r') as f:
        txt = f.read().split("\n")[1:] #first line comment
    dCalc = dict([map(str.strip, i.split(":")) for i in txt])

    a,b,_ = dCalc['Basename'].split('-') # a base name `multinact2-geom111-1` will go `GeomData/geom111/multinact2`
    destCalcDir = "{}/{}/{}".format(pesDir, b, a)
    fRes = "{}/{}.res".format(calcDir, dCalc['Basename'])
    sResults = parseResult(fRes)
    if not os.path.exists(destCalcDir): os.makedirs(destCalcDir)  # this should not exists though


    for iFile in glob("{}/*.*".format(calcDir)):
        if os.path.splitext(iFile)[1][1:] in igList: continue  # copy all file except for ones in ignore list
        # rename file, `multinact2-geom111-1` -> `multinact2-geom111`
        oFile = destCalcDir + "/" + re.sub(r'-\d+','',os.path.basename(iFile))
        shutil.copy(iFile, oFile)
    if zipped:                                                                  # archive the folder if specified
        shutil.make_archive(destCalcDir, 'bztar', root_dir=destCalcDir, base_dir='./')
        shutil.rmtree(destCalcDir)
    if isDel:
        writer("Deleting job directory {}...".format(calcDir))
        shutil.rmtree(calcDir)
    return [dCalc["GeomId"],dCalc["CalcId"], destCalcDir, dCalc["StartGId"],sResults]



def createRunJob(molInfo, file):
    txt = '''        #!/usr/bin/python

        import os, subprocess
        from datetime import datetime

        def writeLog(fLog, msg, cont=False): # writes to the log file
            if not cont :
                msg = '{{:.<90}}'.format(datetime.now().strftime("[%d-%m-%Y %I:%M:%S %p]     ") + msg)
            else:
                msg+='\\n'
            fLog.write(msg)
            fLog.flush()


        # first open export.dat file and collect information about exported jobs
        with open("export.dat",'r') as f:
            expDirs = f.read().split("\\n",1)[1].split()[1:]

        mainDirectory = os.getcwd()
        fLog = open("run.log","a", buffering=1)
        fLog.write("Running exported jobs on host - {{}}\\n".format(os.uname()[1]) + "-"*75 + "\\n")

        # now execute each job
        for RunDir in expDirs:
            if os.path.isfile("{{0}}/{{0}}.calc".format(RunDir)):
                writeLog(fLog, "Job already done for "+RunDir, True)
                continue
            elif os.path.isfile("{{0}}/{{0}}.calc_".format(RunDir)):
                writeLog(fLog, "Running Job for "+RunDir)
            else:
                raise Exception("No '.calc' or '.calc_' file found in {{}}".format(RunDir))
            fComBaseFile = RunDir+".com"

            os.chdir(RunDir)
            exitcode = subprocess.call(["{}",fComBaseFile, "-d", "{}", "-W .", "-n", "{}"] + {})
            os.chdir(mainDirectory)

            if exitcode == 0:
                writeLog(fLog, "Job Successful.", True)
                # rename .calc_ file so that it can be imported
                os.rename( "{{0}}/{{0}}.calc_".format(RunDir), "{{0}}/{{0}}.calc".format(RunDir))
            else:
                writeLog(fLog, "Job Failed.", True)

        writeLog(fLog, "All Jobs Completed\\n")
        writeLog(fLog, "."*70, True)
        fLog.close()

        '''.format(molInfo['exe'],molInfo['scrdir'], molInfo['proc'], molInfo['extra'])
    with open(file, 'w') as f:
        f.write(dedent(txt))
    # leading 0 is invalid in py3 but required in py2 to signify octal number, so this explicit syntax is used
    os.chmod(file,0o766)




# use the following code in run.log to run multiple jobs in parallel
def createRunJobParallel(molInfo, file):
    txt = '''        #!/usr/bin/python

        import os, subprocess
        from datetime import datetime
        from multiprocessing import Pool


        # first open export.dat file and collect information about exported jobs
        with open("export.dat",'r') as f:
            expDirs = f.read().split("\\n",1)[1].split()[1:]

        mainDirectory = os.getcwd()
        fLog = open("run.log","a", buffering=1)
        fLog.write("Running exported jobs on host - {{}}\\n".format(os.uname()[1]) + "-"*75 + "\\n")


        def writeLog(msg): # writes to the log file
            msg = datetime.now().strftime("[%d-%m-%Y %I:%M:%S %p]     ") + msg+'\\n'
            fLog.write(msg)

        # now execute each job
        def runMol(RunDir):
            if os.path.isfile("{{0}}/{{0}}.calc".format(RunDir)):
                writeLog("Job already done for "+RunDir)
                return
            elif os.path.isfile("{{0}}/{{0}}.calc_".format(RunDir)):
                writeLog("Job Started for    "+RunDir)
            else:
                raise Exception("No '.calc' or '.calc_' file found in {{}}".format(RunDir))
            fComBaseFile = RunDir + ".com"
            os.chdir(RunDir)  # will be run on 1 processor
            exitcode = subprocess.call(["{}", fComBaseFile, "-d", '{}', "-W ."] +{})
            os.chdir(mainDirectory)

            if exitcode == 0:
                writeLog("Job Successful for "+ RunDir)
                # rename .calc_ file so that it can be imported
                os.rename( "{{0}}/{{0}}.calc_".format(RunDir), "{{0}}/{{0}}.calc".format(RunDir))
            else:
                writeLog("Job Failed for     " + RunDir)


        if __name__=='__main__':
            p = Pool({})   #< put any number for processor
            p.map(runMol,expDirs)

        writeLog("All Jobs Completed\\n"+"-"*90)
        fLog.close()'''.format(molInfo['exe'],molInfo['scrdir'], molInfo['extra'], molInfo['proc'])
    with open(file, 'w') as f:
        f.write(dedent(txt))
    os.chmod(file,0o766)