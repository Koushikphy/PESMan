from __future__ import print_function
import re
import os
import sys
import shutil
import tarfile
import sqlite3 
import itertools
import numpy as np 
from glob import glob
from geometry import geomObj
# initiate the geometry object inside the geometry file  and call the methods from there
# this is benificial for normal mode as the code doesn't have to  initite the object for every geometry


#TODO:1. Create sequencial export


def parseResult(file):
    # reads a file and returns the result as a string
    with open(file, 'r') as f:
        txt = f.read()
    txt = txt.replace('D','E')
    res = re.findall(r"(?:(?<=^)|(?<=\s))([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)(?=\s|$|\n|\r\n)", txt)
    return ' '.join(res)



def genCalcFile(CalcId,GeomId,CalcName,Basename,Desc="",Aux="",fileName= 'tmp'):

    txt = """# This file is automatically generated.Do not edit, unless you are sure of what you are changing.
    CalcId   : {}
    GeomId   : {}
    Name     : {}
    Basename : {}
    Desc     : {}
    Aux      : {}""".format(CalcId,GeomId,CalcName,Basename,Desc,Aux)

    with open(fileName, "w") as f:
        f.write(txt)



def ExportNearNbrJobs(dB, calcTypeId, jobs, exportDir,pesDir, templ, gidList, sidList, depth, constDb, includePath):

    if calcTypeId > 1: # Mrci or nact export
        ExpGeomList = GetExpMrciNactJobs(dB,calcTypeId, jobs, constDb)
    else:
        ExpGeomList = GetExpGeomNearNbr(dB,calcTypeId, gidList, sidList, jobs, depth, constDb, includePath)


    # con = sqlite3.connect(dB)
    # try:
    #     with con:
    with sqlite3.connect(dB) as con:
            con.row_factory=sqlite3.Row
            cur = con.cursor()
            cur.execute('SELECT * from CalcInfo WHERE Id=?',(calcTypeId,))
            InfoRow = cur.fetchone()
            assert InfoRow, "No Info found for CalcType={} found in data base".format(calcTypeId)
            cur.execute("INSERT INTO Exports (Type,CalcType) VALUES (?,?)", (0,calcTypeId))
            exportId = cur.lastrowid

            ExpDir = "{}/Export{}-{}{}".format(exportDir, exportId, InfoRow["type"], calcTypeId)
            if os.path.exists(ExpDir):
                shutil.rmtree(ExpDir)
            os.makedirs(ExpDir)

            expDirs = []
            for ind, (GeomId,StartCalcId) in enumerate(ExpGeomList, start=1):
                bName = ExportCalc(cur, dB, GeomId, calcTypeId,pesDir,ExpDir, InfoRow, templ,StartId=StartCalcId, BaseSuffix=str(ind))
                expDirs.append(bName)


            # if this is successful, then we need to update the Exports table
            cur.execute("UPDATE Exports SET NumCalc=?, ExpDir=?, ExpDT=datetime('now','localtime') WHERE Id=?", (len(expDirs),ExpDir,exportId))

            lExpCalc = [[exportId, ExpGeomList[i][0], expDirs[i]] for i in range(len(expDirs))]
            cur.executemany("INSERT INTO ExpCalc (ExpId,GeomId,CalcDir) VALUES (?,?,?)",lExpCalc)

            fExportDat = ExpDir + "/export.dat"
            with open(fExportDat,'w') as f:
                f.write("# Auto generated file. Please do not modify\n"+ ' '.join(map(str,[exportId]+expDirs)))

            # change mode of this file to read-only to prevent accidental writes
            os.chmod(fExportDat,0444)

            fPythonFile =   "{}/RunJob{}.py".format(ExpDir, exportId)
            shutil.copy("RunJob.py", fPythonFile)
            os.chmod(fPythonFile,0766)
            print("PESMan export successful: %s jobs exported"%len(ExpGeomList))
    # except Exception as e:
    #     print("Can't export %s"%e)
    # finally :
    #     con.close()



def GetExpGeomNearNbr(dB,CalcTypeId,GidList=[],SidList=[],jobs=1,maxDepth=0,ConstDb="",bIncludePath=False):


    # try:
    with sqlite3.connect(dB) as con:
            cur = con.cursor()
            # notice getting GeomId,Id to easily feed into dictionary
            cur.execute("SELECT GeomId,Id FROM Calc WHERE CalcId=?",(CalcTypeId,))
            calcRow = cur.fetchall()

            # a set of geomIds that is already done
            CalcGeomIds = set([geomId for geomId,_ in calcRow ])
            DictCalcId  = dict(calcRow)

            # set of geomIds that will be excluded from exporting
            ExcludeGeomIds = CalcGeomIds.copy()

            if not bIncludePath:
                cur.execute("SELECT Id FROM Geometry WHERE tags LIKE '%path%'")
                ExcludeGeomIds.update(cur.fetchall())

            cur.execute("SELECT ID FROM Exports WHERE Status=0 and CalcType=?",(CalcTypeId,))
            ids = cur.fetchall()
            for expId in ids:
                cur.execute("SELECT GeomId FROM ExpCalc WHERE ExpId=?",expId) #<-- expid already a tuple
                thisList = [i[0] for i in cur.fetchall()]
                ExcludeGeomIds.update(thisList) #<-- returns a list of tuples, onelist for one filed i.e. GeomId

            print(ExcludeGeomIds,CalcGeomIds)
        #--------------------------------------------------------------------------------
            # lPrblmGeomIds = []
            # ExcludeGeomIds.update(lPrblmGeomIds)
        #--------------------------------------------------------------------------------

            DictStartId = {}
            GidListNew = []

            for g,s in itertools.izip_longest(GidList,SidList):
                if s==None: s=-1
                DictStartId[g] = s
                if g in ExcludeGeomIds:
                    GidListNew.append(0)  
                else:
                    GidListNew.append(g)


            sql = "SELECT Id,Nbr FROM Geometry "
            if GidListNew and ConstDb :
                sql += "where id in (" + ",".join([str(i) for i in GidListNew]) + ") and (" + ConstDb + ")"
            elif GidListNew and not ConstDb:
                sql += "where id in (" + ",".join([str(i) for i in GidListNew]) + ")"
            elif not GidListNew and ConstDb:
                sql += "where "  + ConstDb
            cur.execute(sql)

            # this is only useful only if one gives jobs number less than the gid list length
            # if GidListNew: 
            #     # so when gid list given cur is simple list o/w cur is sqlite iterator. 
            #     # is this bad?,  the cur sqlite instance is not needed after this point
            #     cur = cur.fetchall() 
            #     jobs = len(cur)
            expGClist = []
            # ExcludeGeomIds and CalcGeomIds are sets for faster searching
            for GeomId, nbrList in cur:
                if len(expGClist)==jobs: break     # got all the geometries needed
                if GeomId in ExcludeGeomIds: continue # geometry already exist, skip

                for depth, nId in enumerate(nbrList.split(), start=1):
                    NbrId = int(nId)
                    if maxDepth and (depth>maxDepth): break 
                    if GidListNew and DictStartId[GeomId]>=0: # only if start id is negetive then we have to search neighbour list
                        NbrId = DictStartId[GeomId]
                        if not NbrId: # zero startid
                            expGClist.append([GeomId, 0])
                            break

                    if NbrId in CalcGeomIds: #nbrid done?
                        expGClist.append([GeomId, DictCalcId[NbrId]])
                        break # got one match now don't search for other neighbours

        # preventing null exports
    assert len(expGClist), "No exportable geometries found"
    return expGClist
    # except Exception as e:
    #     print("Can't export %s"%e)
    # finally :
    #     con.close()




def GetExpMrciNactJobs(Db,CalcTypeId,jobs=50,ConstDb=""):

    # try:
    with sqlite3.connect(dB) as con:
            cur = con.cursor()

            cur.execute("SELECT GeomId FROM Calc WHERE CalcId=?",(CalcTypeId,))
            CalcGeomIds = set(cur.fetchall())
            ExcludeGeomIds = CalcGeomIds.copy()  # jobs that is already done.

            cur.execute("SELECT ID FROM Exports WHERE status=0 and CalcType=?",(CalcTypeId,))
            for expId in cur:  # jobs that is exported but not done
                cur.execute("SELECT GeomId FROM ExpCalc WHERE ExpId=?",expId)
                ExcludeGeomIds.update(cur.fetchall())

        #--------------------------------------------------------------------------------
            # lPrblmGeomIds = []
            # ExcludeGeomIds.update(lPrblmGeomIds)
        #--------------------------------------------------------------------------------
            if ConstDb:
                cur.execute("SELECT Id FROM Geometry where " + ConstDb )
                ConstGeomIds = set(cur.fetchall())

            expGClist = []

            cur.execute("SELECT Id,GeomId FROM Calc WHERE CalcId = 1")
            for StartId, GeomId in cur:
                if ConstDb and (GeomId not in ConstGeomIds): # this is a small list so checking it before excludelist
                    continue
                if (GeomId not in ExcludeGeomIds):
                    expGClist.append([GeomId, StartId])
                    if len(expGClist)==jobs: # got everything needed
                        break         

        # preventing null exports
    assert len(expGClist), "No exportable geometries found"
    return expGClist
    # except Exception as e:
    #     print("Can't export %s"%e)
    # finally :
    #     con.close()



def ExportCalc(cur, Db,GeomId,CalcTypeId,DataDir,ExpDir, InfoRow, ComTemplate="",StartId=0,BaseSuffix=""):


    # GeomId and CalcTypeId check
    cur.execute('SELECT * from Geometry WHERE Id=?',(GeomId,))
    GeomRow = cur.fetchone()

    # removed al lot of things from here

    if ComTemplate:
        with open(ComTemplate,'r') as f:  InpTempl = f.read()
    else:
        InpTempl = InfoRow["InpTempl"]

    # if StartId is non-zero, then it must exist in Calc table.
    if StartId:
        cur.execute('SELECT * from Calc WHERE Id=?',(StartId,))
        StartCalcRow = cur.fetchone()
        # pickup details from here -- needed for completing template file
        StartGId = StartCalcRow["GeomId"]
        StartDir = StartCalcRow["Dir"]
        c,a,b = StartDir.split("/")
        StartBaseName = "{}-{}".format(b,a)
    else:
        StartGId = 0


    # decide basename needed for generated files
    BaseName = "{}{}-geom{}-".format(InfoRow["Type"], CalcTypeId, GeomId) + BaseSuffix
    ExportDir = ExpDir + "/" + BaseName
    os.makedirs(ExportDir)


    # write them out
    # for calc file, we will generate it as .calc_ <--- note extra underscore at end
    # this is to safegaurd against faulty imports.
    # this should be renamed to .calc upon successful run
    fCalc = ExportDir + "/" + BaseName + ".calc_"  # <-- extra underscore
    fXYZ  = ExportDir + "/" + BaseName + ".xyz"
    # get these file writes inside of there respective functions
    genCalcFile(CalcTypeId,GeomId,InfoRow["Type"],BaseName,Desc="",Aux="Start GId - " + str(StartGId), fileName=fCalc)
    geomObj.createXYZfile(GeomRow, filename = fXYZ)  #< -- everything is done from outside, the geometry file



    # if wfn file needs to be copied from elsewhere, do that now
    if StartId:
        if os.path.isdir(StartDir): # not in zipped format, copy it to a new name
            shutil.copy(StartDir+ "/%s.wfu"%StartBaseName, ExportDir+"/%s.wfu"%BaseName )
        else: # file is in tar
            tar = tarfile.open(StartDir+".tar.bz2")
            tar.extract("./%s.wfu"%StartBaseName, path=ExportDir) # open tar file and rename it
            os.rename(ExportDir+"/%s.wfu"%StartBaseName, ExportDir+"/%s.wfu"%BaseName)

    txt = InpTempl.replace("$F$",BaseName)
    # generate input file
    fInp = ExportDir + "/" + BaseName + ".com" 
    with open(fInp,'w') as f: f.write(txt)
    
    return BaseName




def ImportNearNbrJobs(dB, expFile, DataDir, iGl, isDel, isZipped):
    ExportDir = os.path.abspath(os.path.dirname(expFile))
    # this function is called with the export.dat file and export id is taken from the exofile so we dont have to check if exportid is given or not. It's obviously not given

    with open(expFile,'r') as f:
        dat = f.read().split("\n",1)[1].split(" ") #skip first line
        exportId, calcDirs = dat[0], dat[1:]

    calcDirsDone = set([d for d in calcDirs if os.path.isfile("{0}/{1}/{1}.calc".format(ExportDir, d)) ])
    # con = sqlite3.connect(dB)
    # try:
    #     with con:
    with sqlite3.connect(dB) as con:
            cur = con.cursor()
            cur.execute('SELECT Status FROM Exports WHERE Id=?',(exportId,))
            exp_row = cur.fetchone()
            assert exp_row,        "Export Id = {} not found in data base".format(exportId)
            assert exp_row[0] ==0, "Export Id = {} is already closed.".format(exportId)

            # now obtain list of jobs which can be imported.
            cur.execute("SELECT GeomId,CalcDir FROM ExpCalc where ExpId=?",(exportId,))
            toImportList = cur.fetchall()
            importCount = 0
            for geomId, calcDir in toImportList:
                if calcDir in calcDirsDone:

                    dirFull = ExportDir + "/" + calcDir
                    cFiles = glob(dirFull+"/*.calc")
                    assert len(cFiles)==1, "{} must have 1 calc file but has {}.".format(dirFull, len(cFiles))

                    print("Importing ...{}...".format(dirFull), end='')
                    ImportCalc(cur,dirFull,cFiles[0],DataDir, ignoreList=iGl, zipped=isZipped)
                    print("done")

                    cur.execute('DELETE FROM ExpCalc WHERE ExpId=? AND GeomId=? ',(exportId,geomId))
                    importCount += 1
                    
                    if isDel: shutil.rmtree(dirFull)

            sImpGeomIds =''# update what geometries are imported with this exportid, to be handled later
            cur.execute("UPDATE Exports SET ImpDT=datetime('now','localtime'), ImpGeomIds=? WHERE Id=?",(sImpGeomIds,exportId))


            cur.execute("SELECT count(*) FROM ExpCalc WHERE ExpId=?",(exportId,))

            if cur.fetchone()[0]==0:
                cur.execute("UPDATE Exports SET Status=1 WHERE Id=?",(exportId,))
                print('Export Id={} is now closed.'.format(exportId))
                if isDel: shutil.rmtree(ExportDir)
            else :
                print('Export Id={} is not closed.'.format(exportId))

            print("{} Jobs have been successfully imported.".format(importCount))
    # except Exception as e:
    #     print( "Can't complete Import. %s"%e)
    # finally:
    #     con.close()



def ImportCalc(cur,CalcDir,CalcFile,DataDir,ignoreList, zipped):

    # parse calcfile and get basename
    # this is to identify the files to be imported.
    with open(CalcFile,'r') as f:
        txt = f.read().split("\n")[1:] #first line comment
    dCalc = dict([map(str.strip, i.split(":")) for i in txt])

    a,b,_ = dCalc['Basename'].split('-') # a base name `multinact2-geom111-1` will go `GeomData/geom111/multinact2`
    DestCalcDir = DataDir+"/{}/{}".format(b,a)  #  simple trick check throughly
    fRes = "{}/{}.res".format(CalcDir, dCalc['Basename'])
    sResults = parseResult(fRes)
    if not os.path.exists(DestCalcDir):  os.makedirs(DestCalcDir)

    tcalc = (dCalc["GeomId"],dCalc["CalcId"], DestCalcDir, dCalc["Aux"],sResults)
    cur.execute("INSERT INTO Calc (GeomId,CalcId,Dir,AuxFiles,Results) VALUES (?, ?, ?, ?, ?)", tcalc) 

    for iFile in glob("{}/*.*".format(CalcDir)):
        if os.path.splitext(iFile)[1] in ignoreList:  # copy all file except for ignore list
            continue
        oFile = DestCalcDir + "/" + re.sub('-\d+','',os.path.basename(iFile)) 
        shutil.copy(iFile, oFile)
    if zipped:
        shutil.make_archive(DestCalcDir, 'bztar', root_dir=DestCalcDir, base_dir='./')
        shutil.rmtree(DestCalcDir)

