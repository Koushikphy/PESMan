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
def GetExpGeomNearNbr(Db,CalcTypeId,GidSingle=0,GidList=[],SidList=[],totGeom=1,NbrDepth=1,NbrDb="",ConstDb="",bIncludePath=False,Verbose=False):

    with sqlite3.connect(Db) as con:
        cur = con.cursor()
        # not using row factory with the database api
        # notice getting GeomId,Id to easily feed into dictionary
        cur.execute("SELECT GeomId,Id FROM Calc WHERE CalcId=?",(CalcTypeId,))
        calcRow = cur.fetchall()

        if len(calcRow)<totGeom:
         raise Exception("Not enough number of completed calculations present in database")

        # a set of geomIds that is already done
        CalcGeomIds = set([geomId for geomId,_ in calcRow ])
        DictCalcId  = dict(calcRow)

        # set of geomIds that will be excluded from exporting
        ExcludeGeomIds = CalcGeomIds.copy()

        if not bIncludePath:
            cur.execute("SELECT Id FROM Geometry WHERE tags LIKE '%path%'")
            ExcludeGeomIds.update(cur.fetchall())


        #! also adding the status, will trim the expcalc search heavily... Try to get geomids from expcalc
        # cur.execute("SELECT ID FROM Exports WHERE CalcType=?",(CalcTypeId,))
        cur.execute("SELECT ID FROM Exports WHERE status=0 CalcType=?",(CalcTypeId,))
        for expId in cur:
            cur.execute("SELECT GeomId FROM ExpCalc WHERE ExpId=?",(expId,))
                ExcludeGeomIds.update(cur.fetchall())


    #--------------------------------------------------------------------------------
            # lPrblmGeomIds = []
            # ExcludeGeomIds.update(lPrblmGeomIds)
    #--------------------------------------------------------------------------------

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

        # this is only useful only if one gives jobs number less than the gid list length
        # if GidListNew: 
        #     # so when gid list given cur is simple list o/w cur is sqlite iterator. 
        #     # is this bad?,  the cur sqlite instance is not needed after this point
        #     cur = cur.fetchall() 
        #     totGeom = len(cur)

        ExpGeomIdList = []
        ExpCalcIdList = []

        # ExcludeGeomIds and CalcGeomIds are sets for faster searching
        for GeomId, nbrList in cur:
            if len(ExpGeomIdList)==totGeom: break

            # don't export if GeomId already inside exported list.. Though this should not have happened
            # if GeomId in ExpGeomIdList: continue
            
            if GeomId in ExcludeGeomIds: continue

            for depth, nId in enumerate(nbrList.split(), start=1):
                nId = int(nId)
                if not maxDepth and (depth>maxDepth): break 

                if GidListNew: # can I get some of this block out of this loop?
                    if DictStartId[GeomId] > 0:
                        NbrId = DictStartId[GeomId]
                    elif DictStartId[GeomId] < 0:
                        NbrId = nId
                    else:
                        NbrId = 0
                else: 
                    NbrId = nId

                if not NbrId:
                    ExpGeomIdList.append(GeomId)
                    ExpCalcIdList.append(0)
                    break

                if NbrId in CalcGeomIds:
                    ExpGeomIdList.append(GeomId)
                    ExpCalcIdList.append(DictCalcId[NbrId])
                    break # got one match now don't search for other neighbours


    # preventing null exports
    assert len(ExpGeomIdList), "Can't export any geometries"
    return zip(ExpGeomIdList, ExpCalcIdList)




def GetExpMrciNactJobs(Db,CalcTypeId,MaxGeom=50,ConstDb="",Verbose=False):
   """ Returns a list of geometries for MRCI or NACT calc- to be exported.
       A list of (GeomId,CalcId) is returned where
          GeomId : geometry to be exported
          CalcId : the id in calc table which corresponds to calc of calctypeid = 1 of the GeomId.
       This will return an empty list if it can not export.
   """

   misc.CheckFileAccess(Db,bRead=True,bAssert=True)
   with sqlite3.connect(Db) as con:

      con.row_factory=sqlite3.Row
      cur = con.cursor()

      # first collect list of geometries for which calculations have been done
      cur.execute("SELECT Id,GeomId FROM Calc WHERE CalcId=?",(CalcTypeId,))
      lrow = cur.fetchall()

      # create a list of geometry ids of completed calculations
      CalcGeomIds = []
      for row in lrow:
         CalcGeomIds.append(row["GeomId"])

      ExcludeGeomIds = []
      # sort CalcGeomIds list so that binary search can be done on it
      # this is important; linear search becomes pretty slow.
      CalcGeomIds.sort()
      ExcludeGeomIds.extend(CalcGeomIds)

      # look into exports table and build a list of geometries which must be
      # excluded because they are already computed or already exported.
      # ExpCalc table keeps a list of geometries already exported.
      cur.execute("SELECT * FROM Exports WHERE CalcType=?",(CalcTypeId,))
      lrow = cur.fetchall()
      for row in lrow:
         cur.execute("SELECT GeomId FROM ExpCalc WHERE ExpId=?",(row['Id'],))
         lgeom = cur.fetchall()
         for lg in lgeom:			   
            ExcludeGeomIds.append(lg['GeomId'])   

      # Define a list of geometries which are problematic so that they are 
      # not exported. It is assumed that they are already removed from
      # the 'calc' table of the database.
      lPrblmGeomIds = []

      if CalcTypeId == 2:    # only to be seen for MRCI jobs
         ExcludeGeomIds.extend(lPrblmGeomIds)
   
      # sort this list so that binary search can be done on it
      ExcludeGeomIds.sort()


      if ConstDb:
         sConst = " where " + ConstDb
      else:
         sConst = ""

      cur.execute("SELECT Id FROM Geometry" + sConst)
      lgeomcon = cur.fetchall()

      ConstGeomIds = []
      for lg in lgeomcon:
          ConstGeomIds.append(lg['Id'])

      ConstGeomIds.sort()

      # initialize the the list of geometries which can be exported
      # the corresponding list contains calcid of the same geoms of calc-id = 1
      ExpGeomIdList = []
      ExpCalcIdList = []

      cur.execute("SELECT Id,GeomId FROM Calc WHERE CalcId = 1")
      row = cur.fetchone()
      while row:
         GeomId = row["GeomId"]
	 StartId = row["Id"]

	 # the geomid must not be in the exclude list
         if GeomId not in ExcludeGeomIds and GeomId in ConstGeomIds:
	    ExpGeomIdList.append(GeomId)
	    ExpCalcIdList.append(StartId)

         # fetch next one
         row = cur.fetchone()
         if len(ExpGeomIdList) == MaxGeom:
            # exit if max jobs is reached
            break

      return zip(ExpGeomIdList,ExpCalcIdList)