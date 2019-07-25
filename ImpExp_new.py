import re
import sqlite3 
import numpy as np 
import itertools


def parseResult(file):
    # reads a file and returns the result as a string
    with open(file, 'r') as f:
        txt = f.read()
    txt = txt.replace('D','E')
    res = re.findall(r"(?:(?<=^)|(?<=\s))([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)(?=\s|$|\n|\r\n)", txt)
    return ' '.join(res)





#! Gurantee that no blank export is done
#! Put calcid in expcalc
#! remove gidsingle
def GetExpGeomNearNbr(Db,CalcTypeId,GidSingle=0,GidList=[],SidList=[],MaxGeom=50,NbrDepth=1,NbrDb="",ConstDb="",bIncludePath=False,Verbose=False):
    with sqlite3.connect(Db) as con:
        cur = con.cursor()
        # not using row factory with the database api
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


        #! insert geomid into expcalc, so this block can be more efficient, for now keeping it untouched
        #! also adding the status, will trim the expcalc search heavily
        # cur.execute("SELECT ID FROM Exports WHERE CalcType=?",(CalcTypeId,))
        cur.execute("SELECT ID FROM Exports WHERE status=0 CalcType=?",(CalcTypeId,))
        for expId in cur:
            cur.execute("SELECT GeomId FROM ExpCalc WHERE ExpId=?",(expId,))
                ExcludeGeomIds.update(cur.fetchall())


#--------------------------------------------------------------------------------
        lPrblmGeomIds = []
#--------------------------------------------------------------------------------

        ExcludeGeomIds.update(lPrblmGeomIds)


        ExpGeomIdList = []
        ExpCalcIdList = []

        DictStartId = {}
        GidListNew = []


        for g,s in itertools.izip_longest(GidList,SidList):
            if (g in ExcludeGeomIds) or (s==None):
                DictStartId[g] = -1
                GidListNew.append(0)    #<--- why adding geomlist here?
            else:
                DictStartId[g] = s
                GidListNew.append(geom)


        ########################### New style of neighbour searching ####################################
        sql = "select Id,Nbr form Geometry"
        if GidListNew and ConstDb :
            sql += "where id in (" + ",".join([str(i) for i in GidListNew]) + ") and (" + ConstDb + ")"
        elif GidListNew and not ConstDb:
            sql += "where id in (" + ",".join([str(i) for i in GidListNew]) + ")"
        elif not GidListNew and ConstDb:
            sql += "where "  + ConstDb


        cur.execute(sql)

        # ExcludeGeomIds and CalcGeomIds are sets for faster searching
        for GeomId, nbrList in cur:
            nbrList = nbrList.split()

            # don't export if GeomId already inside exported list.. Though this should not have happened
            if GeomId in ExpGeomIdList:   continue
            
            if GeomId in ExcludeGeomIds: continue

            for depth, nId in enumerate(nbrList, start=1):

                if not maxDepth and (depth>maxDepth):
                    break

                if GidListNew: # can I get some of this block out of this loop?
                    if DictStartId[GeomId] > 0:
                        NbrId = DictStartId[GeomId]
                    elif DictStartId[GeomId] < 0:
                        NbrId = nId
                    else:
                        NbrId = 0
                else: 
                    NbrId = nId


                if NbrId in CalcGeomIds:
                    ExpGeomIdList.append(GeomId)
                    ExpCalcIdList.append(DictCalcId[NbrId])
                    break # got one match now don't search for other neighbours

                if not NbrId: # this should get out of this loop
                    ExpGeomIdList.append(GeomId)
                    ExpCalcIdList.append(0)
                    break
    # preventing null exports
    assert len(ExpGeomIdList), "Can't export any geometries"
    return zip(ExpGeomIdList, ExpCalcIdList)