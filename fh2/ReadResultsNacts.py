
import sqlite3

def CollectGeoms(Db):

    """ Routine that returns a list of tuples containing rho,theta,phi
       of the geometries whose nact calcs are done."""

    with sqlite3.connect(Db) as con:
      con.row_factory = sqlite3.Row
      cur = con.cursor()
      cur.execute("SELECT geomid from Calc where CalcId = 3")
      GeomRow = cur.fetchall() 

      assert (len(GeomRow) > 0)
  
      lgid = []

      for gid in GeomRow:
        lgid.append(gid["geomid"])

      lgeoms = []

      for gid in lgid:
        cur.execute("SELECT rho,theta,phi from Geometry where id = ?",(gid,))
        GeomRow = cur.fetchall() 
        assert (len(GeomRow) == 1)
        geomrow = GeomRow[0]
        lgeoms.append((geomrow["rho"],geomrow["theta"],geomrow["phi"]))

    return lgeoms


def readres(Db,rho,theta,phi):
    
    """ Routine to read results from database for a given theta and
        phi and export the nac results in terms of a list."""

    flag = 0
    with sqlite3.connect(Db) as con:
      con.row_factory = sqlite3.Row
      cur = con.cursor()
      cur.execute("SELECT id from Geometry where rho =? and theta =? and phi=?",(rho,theta,phi))
      GeomRow = cur.fetchall() 
      assert (len(GeomRow) == 1)
      geomrow = GeomRow[0]

      cur.execute("SELECT results from Calc where CalcId = 3 and GeomId=?",(geomrow["id"],))
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
  
  Db = "fh2db.db"
  dth = 0.03*pi/180.0
  dph = 0.03*pi/180.0
  drh = 0.01

  lgeoms = CollectGeoms(Db)

  lgeoms.sort()

  print "Obtaining results...Please wait"

  rhoprev = 0.0
  thetaprev = 0.0

  for geoms in lgeoms:
   
        flag = 0
        rho,theta,phi = geoms

        lres = readres(Db,rho,theta,phi)
        assert(len(lres) == 9)
	lres12 = []

	i=0
	while i<9:
	    lres12.append(lres[i])
	    i+=1
        lres13 = []

        i=0

        squtau12 = 0.0
        while i<9:
          squtau12 += lres[i]*lres[i]
          i+=1
        Taumod12 = math.sqrt(squtau12)



        thpl = theta + dth
        gthpl = geometry.Geometry(rho=rho,theta=thpl,phi=phi,degs = False)
        lc = gthpl.to_cart()

        xpl = [i for i in range(9)]
        xpl[0]=0.0; xpl[3]=0.0; xpl[6]=0.0
        at1,(xpl[1],xpl[2]) = lc[0]
        at2,(xpl[4],xpl[5]) = lc[1]
        at3,(xpl[7],xpl[8]) = lc[2]

        thmi = theta - dth
        gthmi = geometry.Geometry(rho=rho,theta=thmi,phi=phi,degs = False)
        lc = gthmi.to_cart()

        xmi = [i for i in range(9)]
        xmi[0]=0.0; xmi[3]=0.0; xmi[6]=0.0
        at1,(xmi[1],xmi[2]) = lc[0]
        at2,(xmi[4],xmi[5]) = lc[1]
        at3,(xmi[7],xmi[8]) = lc[2]
        xgradt = []

        i=0
        while i<9:
            xgr = (xpl[i]-xmi[i])/2.0/dth
            xgradt.append(xgr)
            i+=1

        phpl = phi + dph
        gphpl = geometry.Geometry(rho=rho,theta=theta,phi=phpl,degs = False)
        lc = gphpl.to_cart()

        xpl = [i for i in range(9)]
        xpl[0]=0.0; xpl[3]=0.0; xpl[6]=0.0
        at1,(xpl[1],xpl[2]) = lc[0]
        at2,(xpl[4],xpl[5]) = lc[1]
        at3,(xpl[7],xpl[8]) = lc[2]

        phmi = phi - dph
        gphmi = geometry.Geometry(rho=rho,theta=theta,phi=phmi,degs = False)
        lc = gphmi.to_cart()

        xmi = [i for i in range(9)]
        xmi[0]=0.0; xmi[3]=0.0; xmi[6]=0.0
        at1,(xmi[1],xmi[2]) = lc[0]
        at2,(xmi[4],xmi[5]) = lc[1]
        at3,(xmi[7],xmi[8]) = lc[2]
        xgradp = []

        i=0
        while i<9:
            xgr = (xpl[i]-xmi[i])/2.0/dph
            xgradp.append(xgr)
            i+=1

        rhpl = rho + drh
        grhpl = geometry.Geometry(rho=rhpl,theta=theta,phi=phi,degs = False)
        lc = grhpl.to_cart()

        xpl = [i for i in range(9)]
        xpl[0]=0.0; xpl[3]=0.0; xpl[6]=0.0
        at1,(xpl[1],xpl[2]) = lc[0]
        at2,(xpl[4],xpl[5]) = lc[1]
        at3,(xpl[7],xpl[8]) = lc[2]

        rhmi = rho - drh
        grhmi = geometry.Geometry(rho=rhmi,theta=theta,phi=phi,degs = False)
        lc = grhmi.to_cart()

        xmi = [i for i in range(9)]
        xmi[0]=0.0; xmi[3]=0.0; xmi[6]=0.0
        at1,(xmi[1],xmi[2]) = lc[0]
        at2,(xmi[4],xmi[5]) = lc[1]
        at3,(xmi[7],xmi[8]) = lc[2]
        xgradr = []

        i=0
        while i<9:
            xgr = (xpl[i]-xmi[i])/2.0/drh
            xgradr.append(xgr)
            i+=1

	Taur12 = 0.0
	Taut12 = 0.0
	Taup12 = 0.0

	i=0
	while i<9:
    	    Taur12 += xgradr[i]*lres12[i]

	    Taut12 += xgradt[i]*lres12[i]

	    Taup12 += xgradp[i]*lres12[i]
	    i+=1

	Taur12 = "{0:9.8f}".format(math.fabs(Taur12))
	Taut12 = "{0:9.8f}".format(math.fabs(Taut12))
	Taup12 = "{0:9.8f}".format(math.fabs(Taup12))

        if rho == rhoprev and theta != thetaprev:
           flag = 1
        
        rhoprev = rho
        thetaprev = theta 
        theta = theta*180.0/pi
        phi = phi*180.0/pi

        if flag:
 	    fr = open(ResDir + "/TAU-RHO" + "/TauRho.dat", "a")
            fr.write("\n")
            fr.close()
 
  	    ft = open(ResDir + "/TAU-THETA" + "/TauTheta.dat", "a")
            ft.write("\n")
            ft.close()

	    fp = open(ResDir + "/TAU-PHI" + "/TauPhi.dat", "a")
            fp.write("\n")
            fp.close()

	    fp = open(ResDir + "/TAU" + "/Tau.dat", "a")
            fp.write("\n")
            fp.close()
            
	fr = open(ResDir + "/TAU-RHO" + "/TauRho.dat", "a")
	fr.write(str(rho)+"\t"+str(theta)+"\t"+str(phi) + "\t"+ str(Taur12)+'\n')
        fr.close()

	ffr = open(ResDir + "/TAU-RHO" + "/TauRho_theta" + str(theta) + ".dat", "a")
	ffr.write(str(rho)+"\t"+str(theta)+"\t"+str(phi) + "\t"+ str(Taur12)+'\n')
        ffr.close()

	ft = open(ResDir + "/TAU-THETA" + "/TauTheta.dat", "a")
	ft.write(str(rho)+"\t"+str(theta)+"\t"+str(phi) + "\t"+ str(Taut12)+'\n')
        ft.close()

	fft = open(ResDir + "/TAU-THETA" + "/TauTheta_theta" + str(theta) + ".dat", "a")
	fft.write(str(rho)+"\t"+str(theta)+"\t"+str(phi) + "\t"+ str(Taut12)+'\n')
        fft.close()

	fp = open(ResDir + "/TAU-PHI" + "/TauPhi.dat", "a")
	fp.write(str(rho)+"\t"+str(theta)+"\t"+str(phi) + "\t"+ str(Taup12)+'\n')
        fp.close()
 
	ffp = open(ResDir + "/TAU-PHI" + "/TauPhi_theta" + str(theta) + ".dat", "a")
	ffp.write(str(rho)+"\t"+str(theta)+"\t"+str(phi) + "\t"+ str(Taup12)+'\n')
        ffp.close()
 
	fp = open(ResDir + "/TAU" + "/Tau.dat", "a")
	fp.write(str(rho)+"\t"+str(theta)+"\t"+str(phi) + "\t"+ str(Taumod12)+'\n')
        fp.close()
 
	ffp = open(ResDir + "/TAU" + "/Tau_theta" + str(theta) + ".dat", "a")
	ffp.write(str(rho)+"\t"+str(theta)+"\t"+str(phi) + "\t"+ str(Taumod12)+'\n')
        ffp.close()
 










