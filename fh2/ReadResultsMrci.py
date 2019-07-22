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

    asymap = -100.7074625
    asymapp = -100.7074466
    asymqap = -100.70923576
    asymqapp = -100.70921838

    txt = ""

    for i in range(number):
        rho = col[i][0]
        theta = col[i][1] * 180/math.pi
        phi = col[i][2] * 180/math.pi
        result = col[i][3]
        calcid = col[i][4]
	result = result.split(" ")
	result = [float(res) for res in result]

        if len(result) == 6:
           result = [u - asymap for u in result[:2]] + [result[2] - asymapp] +  [u - asymqap for u in result[3:5]] + [result[5] - asymqapp]
        elif len(result) == 4:
           result = [u - asymap for u in result[:2]] + [result[1] - asymap] + [u - asymqap for u in result[2:4]] + [result[3] - asymqap]
        else:
           print "wrong 'result' array..."


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


