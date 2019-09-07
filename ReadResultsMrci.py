import geometry
import math
import sqlite3
import os
import sys
import bisect

def CollectGeoms(Db):

    """ Routine that returns a list of tuples containing rho,theta,phi
       of the geometries whose multi calcs are done."""
 
    with sqlite3.connect(Db) as con:
      con.row_factory = sqlite3.Row
      cur = con.cursor()
      cur.execute("SELECT id,geomid,results from Calc where CalcId = 2")
      CalcRow = cur.fetchall() 

      assert (len(CalcRow) > 0)
  
      cur.execute("SELECT id,rho,theta,phi from Geometry")
      GeomRow = cur.fetchall()

      lgid = []
      for gid in GeomRow:
        lgid.append(gid["id"])

      lgid.sort()
   
      lgeoms = []
      for ii in CalcRow:
          gid = ii["geomid"]
          i = bisect.bisect_left(lgid,gid)
          if i != len(lgid) and lgid[i] == gid:
             lgeoms.append((GeomRow[i][1],GeomRow[i][2],GeomRow[i][3],ii["Results"],ii["id"]))
    return lgeoms
    
    
if __name__ == "__main__":

    col=CollectGeoms("fh2db.db")
    col.sort()
    number=len(col)

    ResDir = "Result_files_Mrci"
    if not os.path.exists(ResDir):
     os.makedirs(ResDir)

    asym = -100.7074720
    asymq = -100.7092462
    txt = ""

    for i in range(number):
        rho = col[i][0]
        theta = col[i][1] * 180/math.pi
        phi = col[i][2] * 180/math.pi
        result = col[i][3]
        calcid = col[i][4]
	result = result.split(" ")
	result = [float(res) for res in result]
        result = [u - asym for u in result[:4]] + [u - asymq for u in result[4:]]
	result = ["{0:.8f}".format(u) for u in result]

        with open(ResDir + "/Enr_{}.dat".format(theta), "a") as f:
            
            txt1 = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(rho,theta,phi,*result)
            
            if i < (number-1) and col[i][1] != col[i+1][1]:
                txt1 += "\n"
            
            f.write(txt1)


	txt += "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(rho,theta,phi,*result)

        if i < (number-1) and col[i][1] != col[i+1][1]:
	   txt += "\n"

	
    with open(ResDir + "/Enr.dat","w") as f:

        f.write(txt)


