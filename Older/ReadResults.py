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
      cur.execute("SELECT geomid,energy,somatel,soener from RESULTS")
      CalcRow = cur.fetchall() 

      cur.execute("SELECT id,sr,cr,theta from Geometry")
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
             lgeoms.append((GeomRow[i]["sr"],GeomRow[i]["cr"],GeomRow[i]["theta"],ii["energy"],ii["somatel"],ii["soener"]))
    return lgeoms
    
    
if __name__ == "__main__":

   col = CollectGeoms("fh2db.db")
   col.sort()
   
   ResDir = "Result_files_Adia"
   SODir = "Result_files_SOEner"
   
   if not os.path.exists(ResDir):
      os.makedirs(ResDir)

   if not os.path.exists(SODir):
      os.makedirs(SODir)      

   pi = math.pi

   asymap = -100.7074625
   asymapp = -100.7074466
   asymqap = -100.70923576
   asymqapp = -100.70921838

   so_asym = -100.70804746

   to_kcal = 627.503

   for i in range(len(col)):
      sr,cr,theta = col[i][0],col[i][1],col[i][2]*180.0/pi
      ener,somat,soener = col[i][3],col[i][4],col[i][5]

      ener = [float(u) for u in ener.split(" ")]
      ener = [u - asymap for u in ener[:2]] + [ener[2] - asymapp] +  [u - asymqap for u in ener[3:5]] + [ener[5] - asymqapp]
      ener = [u*to_kcal for u in ener]

      soener = [(float(u)-so_asym)*to_kcal for u in soener.split(" ")]
     
      #   calcid = col[i][4]
	   #   result = result.split(" ")
	   #   result = [float(res) for res in result]

      #   if len(result) == 6:
      #      result = [u - asymap for u in result[:2]] + [result[2] - asymapp] +  [u - asymqap for u in result[3:5]] + [result[5] - asymqapp]
      #   elif len(result) == 4:
      #      result = [u - asymap for u in result[:2]] + [result[1] - asymap] + [u - asymqap for u in result[2:4]] + [result[3] - asymqap]
      #   else:
      #      print "wrong 'result' array..."


	   #   result = ["{0:.8f}".format(u*to_kcal) for u in result]

      with open(ResDir + "/Enr_r-{}.dat".format(sr),"a") as f:

            txt = "{}\t{}\t{:12.8f}\t{:12.8f}\t{:12.8f}\t{:12.8f}\t{:12.8f}\t{:12.8f}\n".format(sr,cr,*ener)

            f.write(txt)

      with open(SODir + "/Enr-SO_r-{}.dat".format(sr),"a") as f:

            txt = "{}\t{}\t{:12.8f}\t{:12.8f}\t{:12.8f}\t{:12.8f}\t{:12.8f}\t{:12.8f}\n".format(sr,cr,*soener)

            f.write(txt)



