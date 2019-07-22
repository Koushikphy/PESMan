
import sqlite3

def CollectGeoms(Db):

    """ Routine that returns a list of tuples containing rho,phi
       of the geometries whose nact calcs are done."""

    with sqlite3.connect(Db) as con:
      con.row_factory = sqlite3.Row
      cur = con.cursor()
      cur.execute("SELECT geomid from Calc where CalcId = 2")
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
        lgeoms.append((geomrow["rho"],geomrow["phi"]))

    return lgeoms


def readres(Db,rho,phi):
    
    """ Routine to read results from database for a given 
        phi and export the nac results in terms of a list."""

    flag = 0
    with sqlite3.connect(Db) as con:
      con.row_factory = sqlite3.Row
      cur = con.cursor()
      cur.execute("SELECT id from Geometry where rho =? and phi=?",(rho,phi))
      GeomRow = cur.fetchall() 
      assert (len(GeomRow) == 1)
      geomrow = GeomRow[0]

      cur.execute("SELECT results from Calc where CalcId = 2 and GeomId=?",(geomrow["id"],))
      CalcRow = cur.fetchall() 
      assert (len(CalcRow) <= 1)
      lres = []
      if CalcRow:
	 calrow = CalcRow[0]
	 sres = calrow["results"]
	 sres = sres.split()
	 lres = [float(s) for s in sres]
    return lres
      

if __name__ == "__main__":

  import math
  import geometry
  import os

  pi = math.pi

  ResDir = "Result_files_Nact"
  if not os.path.isdir(ResDir):
    os.mkdir(ResDir)
  
  Db = "no2db.db"

  lgeoms = CollectGeoms(Db)

  lgeoms.sort()

  print "Obtaining results...Please wait"

  aq1 = []
  f = open("coeff_Q1.dat",'r')
  ii = 0
  while ii < 9:
    aq1.append(f.readline())
    ii += 1
  f.close()

  aq2 = []
  f = open("coeff_Q3.dat",'r')
  ii = 0
  while ii < 9:
    aq2.append(f.readline())
    ii += 1
  f.close()

  f = open("input.dat",'r')
  nmass,omass = f.readline().split()
 # omass = f.readline()

  omega = []

  ii = 0
  while ii < 2:
    omega.append(f.readline())
    ii += 1
  f.close()

  aq1 = [float(i) for i in aq1]

  aq2 = [float(i) for i in aq2]

  nmass = float(nmass)

  omass = float(omass)

  omega = [float(i) for i in omega]

  hcross = 0.06350781278

  cminvtinv = 0.001883651 

  ang = 0.529177249 

  omega = [i*cminvtinv for i in omega]

  for i in range(3):

      aq1[i] = (aq1[i] * math.sqrt(hcross/nmass/omega[0]))/ang

      aq2[i] = (aq2[i] * math.sqrt(hcross/nmass/omega[1]))/ang

  for i in range(3,9,1):

      aq1[i] = (aq1[i] * math.sqrt(hcross/omass/omega[0]))/ang

      aq2[i] = (aq2[i] * math.sqrt(hcross/omass/omega[1]))/ang


  rhoprev = 0.0

  for geoms in lgeoms:
   
        flag = 0
        rho,phi = geoms

        lres = readres(Db,rho,phi)
        assert(len(lres) == 18)

	i=0
	lres12_1 = []
	while i<9:
	    lres12_1.append(lres[i])
	    i+=1

        lres12_2 = []
        while i<18:
            lres12_2.append(lres[i])
            i+=1

        Sumsq12_1 = 0.0
        Sumsq12_2 = 0.0

	Tau12q1_1 = 0.0
	Tau12q2_1 = 0.0

	Tau12q1_2 = 0.0
	Tau12q2_2 = 0.0

        Taur12_1 = 0.0
        Taur12_2 = 0.0
        Taup12_1 = 0.0
        Taup12_2 = 0.0

	i=0
	while i<9:   

            Sumsq12_1 += lres12_1[i]*lres12_1[i]
            Sumsq12_2 += lres12_2[i]*lres12_2[i]
     
            Tau12q1_1 += aq1[i]*lres12_1[i]
            Tau12q2_1 += aq2[i]*lres12_1[i]
            Tau12q1_2 += aq1[i]*lres12_2[i]
            Tau12q2_2 += aq2[i]*lres12_2[i]

            Taur12_1 += math.cos(phi)*aq1[i]*lres12_1[i] + math.sin(phi)*aq2[i]*lres12_1[i]
            Taup12_1 += -math.sin(phi)*aq1[i]*lres12_1[i] + math.cos(phi)*aq2[i]*lres12_1[i]
            Taur12_2 += math.cos(phi)*aq1[i]*lres12_2[i] + math.sin(phi)*aq2[i]*lres12_2[i]
            Taup12_2 += -math.sin(phi)*aq1[i]*lres12_2[i] + math.cos(phi)*aq2[i]*lres12_2[i]

	    i += 1

        Tau12_1 = "{0:9.8f}".format(math.sqrt(Sumsq12_1))
        Tau12_2 = "{0:9.8f}".format(math.sqrt(Sumsq12_2))

        Tau12q1_1 = "{0:9.8f}".format(math.fabs(Tau12q1_1))                 
        Tau12q2_1 = "{0:9.8f}".format(math.fabs(Tau12q2_1))
        Tau12q1_2 = "{0:9.8f}".format(math.fabs(Tau12q1_2))                 
        Tau12q2_2 = "{0:9.8f}".format(math.fabs(Tau12q2_2))
               
        Taur12_1 = "{0:9.8f}".format(math.fabs(Taur12_1)) 
        Taup12_1 = "{0:9.8f}".format(math.fabs(Taup12_1))
        Taur12_2 = "{0:9.8f}".format(math.fabs(Taur12_2)) 
        Taup12_2 = "{0:9.8f}".format(math.fabs(Taup12_2))
 
        if rho != rhoprev:
           flag = 1
        
        rhoprev = rho

        Qx = "{0:9.8f}".format(rho*math.cos(phi))
        Qy = "{0:9.8f}".format(rho*math.sin(phi))

        if flag:
 	    ffr = open(ResDir + "/TAU-RHO" + "/TauRho.dat", "a")
            ffr.write("\n")
            ffr.close()
 
 	    ffr = open(ResDir + "/TAU-PHI" + "/TauPhi.dat", "a")
            ffr.write("\n")
            ffr.close()
 
 	    ffr = open(ResDir + "/TAU-Q1" + "/TauQ1.dat", "a")
            ffr.write("\n")
            ffr.close()
 
 	    ffr = open(ResDir + "/TAU-Q2" + "/TauQ2.dat", "a")
            ffr.write("\n")
            ffr.close()
 
            ffr = open(ResDir + "/TAU" + "/Tau.dat", "a")
            ffr.write("\n")
            ffr.close()

	ffr = open(ResDir + "/TAU-RHO" + "/TauRho.dat", "a")
	ffr.write(str(rho) + "\t" + str(phi) + "\t")
	ffr.write(str(Taur12_1)+ "\t" + str(Taur12_2) + "\n")
        ffr.close()
	
	ffr = open(ResDir + "/TAU-PHI" + "/TauPhi.dat", "a")
	ffr.write(str(rho) + "\t" + str(phi) + "\t")
	ffr.write(str(Taup12_1) + "\t" + str(Taup12_2) + "\n")
        ffr.close()


	ffr = open(ResDir + "/TAU-Q1" + "/TauQ1.dat", "a")
	ffr.write(str(rho) + "\t" + str(phi) + "\t")
	ffr.write(str(Tau12q1_1)+ "\t" + str(Tau12q1_2)   + "\n")
        ffr.close()

	ffr = open(ResDir + "/TAU-Q2" + "/TauQ2.dat", "a")
	ffr.write(str(rho) + "\t" + str(phi) + "\t")
	ffr.write(str(Tau12q2_1)+ "\t" + str(Tau12q2_2)  +  "\n")
        ffr.close()

	ffr = open(ResDir + "/TAU" + "/Tau.dat", "a")
	ffr.write(str(rho) + "\t" + str(phi) + "\t")
	ffr.write(str(Tau12_1)+ "\t" + str(Tau12_2) + "\n")
        ffr.close()

 










