
import sqlite3

def CollectGeoms(Db):

    """ Routine that returns a list of tuples containing rho,phi
       of the geometries whose multi calcs are done."""

    with sqlite3.connect(Db) as con:
      con.row_factory = sqlite3.Row
      cur = con.cursor()
      cur.execute("SELECT geomid from Calc where CalcId = 1")
      GeomRow = cur.fetchall() 

      assert (len(GeomRow) > 0)
  
      lgid = []

      for gid in GeomRow:
        lgid.append(gid["geomid"])

      lgeoms = []

      for gid in lgid:
        cur.execute("SELECT rho,phi from Geometry where id = ?",(gid,))
        GeomRow = cur.fetchall() 
        assert (len(GeomRow) == 1)
        geomrow = GeomRow[0]
        lgeoms.append((geomrow["rho"],geomrow["phi"],gid))

    return lgeoms


def readres(Db,rho,phi,gid):
    
    """ Routine to read results from database for a given rho and
        phi and export the multi results in terms of a list."""

    with sqlite3.connect(Db) as con:
      con.row_factory = sqlite3.Row
      cur = con.cursor()

      cur.execute("SELECT results from Calc where CalcId = 1 and GeomId=?",(gid,))
      CalcRow = cur.fetchall() 
      assert (len(CalcRow) == 1)
      lres = []
      calrow = CalcRow[0]
      sres = calrow["results"]
#     sres = sres.split()
#     lres = [float(s) for s in sres]

    return sres
      

if __name__ == "__main__":

  import math
  import geometry
  import os

  print "Obtaining results. Please wait..."

  pi = math.pi

  ResDir = "Result_files_Multi"
  if not os.path.isdir(ResDir):
    os.mkdir(ResDir)
  
  Db = "no2db.db"

  lgeoms = CollectGeoms(Db)

  lgeoms.sort()

  rhoprev = 0.0

  for geoms in lgeoms:
   
        flag = 0
        rho,phi,gid = geoms

        x = rho*math.cos(phi)
        y = rho*math.sin(phi)

        x = "{0:12.6f}".format(x)
        y = "{0:12.6f}".format(y)

        sres = readres(Db,rho,phi,gid)
#       assert(len(lres) == 5)

        if rho != rhoprev:
           flag = 1
        
        rhoprev = rho

        if flag:
 	    f = open(ResDir + "/Enr.dat", "a")
            f.write("\n")
            f.close()

	f = open(ResDir + "/Enr.dat", "a")
	f.write(str(rho)+"\t"+str(phi*180.0/pi) + "\t" + sres + "\n")
        f.close()

	ff = open(ResDir + "/Enr_rho-{}".format(rho) + ".dat", "a")
	ff.write(str(rho)+"\t"+str(phi*180.0/pi) + "\t" + sres + "\n")
        ff.close()


