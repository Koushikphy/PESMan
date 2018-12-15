import misc
import math
import kabsch

def jac2cart(rs,rc,gamma,atom1,atom2,atom3):
   """ Convert to cartesian coordinates in yz plane.
       Molecule will be on yz plane with m1 and m2 lying on y-axis.
       NOTE : coordinates will be in atomic units NOT angstroms """
   h1y = -rs/2.0
   h1z = 0.0
   h2y = rs/2.0
   h2z = 0.0
   h3y = rc*math.cos(gamma)
   h3z = rc*math.sin(gamma)
   lcart = [ (atom1,(h1y,h1z)), (atom2,(h2y,h2z)), (atom3,(h3y,h3z)) ]
   return lcart

class Geometry():
    """A class storing a geometry in hyper-spherical coordinates"""

    # atomic names and masses of atoms in a triatomic molecule.
    # WARN : These are class variables shared by all instances. Do not change them.
    # TODO : Make them immutable
    atom1, mass1 = "H", 1.0
    atom2, mass2 = "H", 1.0
    atom3, mass3 = "H", 1.0

    def __init__(self, rho, theta, phi, angs = False, degs = False, id = 0):
       """ constructor with hs coords
           NOTE: by default atomic units and radians
           set angs = True for angstroms and degs = True for degrees """
       self.rho = rho
       if angs:
          self.rho = misc.ToBohrs(self.rho)
       self.theta = theta
       self.phi = phi
       if degs:
          self.theta = misc.ToRad(self.theta)
          self.phi = misc.ToRad(self.phi)
       # also set id, useful for later manipulations
       self.id = id

    def __repr__(self):
       """ more exact representation of geometry object """
       return "Geometry({0:10.6f},{1:10.6f},{2:10.6f})".format(self.rho,self.theta,self.phi)

    def __str__(self):
       """ readable representation of geometry object """
       srho = "{0:7.3f} au".format(self.rho)
       stheta = "{0:7.3f} deg".format(misc.ToDeg(self.theta))
       sphi = "{0:7.3f} deg".format(misc.ToDeg(self.phi))
       srho = misc.strip_float(srho)
       stheta = misc.strip_float(stheta)
       sphi = misc.strip_float(sphi)
       sid = ""
       if self.id:
          sid = "geom-" + '{:05d}'.format(self.id)
          sid = "geom-" + str(self.id)
       return sid + "-(" + srho + "," + stheta + "," + sphi + ")"

    def filestr(self):
       """ a representation of geometry object suitable for use as file name """
       srho = "{0:7.3f}".format(self.rho)
       stheta = "{0:7.3f}".format(misc.ToDeg(self.theta))
       sphi = "{0:7.3f}".format(misc.ToDeg(self.phi))
       srho = misc.strip_float(srho)
       stheta = misc.strip_float(stheta)
       sphi = misc.strip_float(sphi)
       sid = ""
       if self.id:
          sid = "geom-" + '{:05d}'.format(self.id)
          sid = "geom" + str(self.id)
       return sid + "-" + srho + "-" + stheta + "-" + sphi

    def to_hsc(self):
        """ return a tuple containing hyper spher coords """
        return (self.rho,self.theta,self.phi)

    def to_jacobi(self):
	""" returns jacobi coordinates of the geometry object 
	    calculate R1, R2, R3 from hyperspherical coords
	    formulas given by Bijit.
            results are in bohrs and radians """

        m1,m2,m3 = Geometry.mass1, Geometry.mass2, Geometry.mass3
        rho,theta,phi = self.rho, self.theta, self.phi
        pi = math.pi

	R1 = math.sqrt(rho*rho*(1.0+math.sin(theta)*math.sin(phi+4.0*pi/3.0))/math.sqrt(3.0)) # H2-H3 distance
	R2 = math.sqrt(rho*rho*(1.0+math.sin(theta)*math.sin(phi-4.0*pi/3.0))/math.sqrt(3.0)) # H1-H3 distance
	R3 = math.sqrt(rho*rho*(1.0+math.sin(theta)*math.sin(phi))/math.sqrt(3.0)) # H1-H2 distance

	if R1 < 1e-10:
	   R1 = 0.0
	if R2 < 1e-10:
	   R2 = 0.0
	if R3 < 1e-10:
	   R3 = 0.0

        y2 = R3
        if R3 != 0.0:
           y3 = (R2*R2 + R3*R3 - R1*R1)/(2.0*R3)
        else:
           y3 = 0.0

        ss = R2*R2 - y3*y3

        if ss > -1e-10 and ss < 0.0:
           ss = 0.0

        z3 = math.sqrt(ss)

        rs = R3

        ycm = y2/2.0
        zcm = 0.0

        rc = math.sqrt((y3-ycm)**2 + (z3-zcm)**2)

	if rc < 1e-10:
	   rc = 0.0

        if rs == 0.0 or rc == 0.0:
           gamma = 0.0
        else:
           val = (rc*rc+(rs*rs/4.0)-R1*R1)/(rc*rs)
           if val > 1.0 and val-1.0 < 1e-10:
              val = 1.0
           if val < -1.0 and abs(val)-1.0 < 1e-10:
              val = -1.0
           gamma=math.acos(val)

	return (rs, rc, gamma)

    def to_cart(self):
        """ Convert to cartesian coordinates in yz plane.
            Molecule will be on yz plane with m2 and m3 lying on z-axis.
            NOTE : coordinates will be in atomic units NOT angstroms """

        at1,at2,at3 = Geometry.atom1,Geometry.atom2,Geometry.atom3
        rho,theta,phi = self.rho, self.theta, self.phi
        pi = math.pi
        eps = 1e-10

	R1 = math.sqrt(rho*rho*(1.0+math.sin(theta)*math.sin(phi+4.0*pi/3.0))/math.sqrt(3.0)) # H2-H3 distance
	R2 = math.sqrt(rho*rho*(1.0+math.sin(theta)*math.sin(phi-4.0*pi/3.0))/math.sqrt(3.0)) # H1-H3 distance
	R3 = math.sqrt(rho*rho*(1.0+math.sin(theta)*math.sin(phi))/math.sqrt(3.0)) # H1-H2 distance

	if R1 < eps:
	   R1 = 0.0
	if R2 < eps:
	   R2 = 0.0
	if R3 < eps:
	   R3 = 0.0

        y1 = 0.0
	z1 = 0.0
	y2 = R3
	z2 = 0.0

	if R3:
           y3 = (R2*R2+R3*R3-R1*R1)/2.0/R3
	else:
	   y3 = 0.0

	ss = R2*R2 - y3*y3

	if ss > -eps and ss < 0.0:
	   ss = 0.0

	z3 = math.sqrt(ss)

        #lcart = [ (at1,(y1,z1)), (at2,(y2,z2)), (at3,(y3,z3)) ]
        #return lcart
        rs,rc,gamma = self.to_jacobi()
        return jac2cart(rs,rc,gamma,at1,at2,at3)


    def krmsd(self,other):
        """ return kabsch RMSD with other geometry.
            other can be either a geometry object or a string of xyz file """
        lc_self = self.to_cart()
        lp = [ y for (x,y) in lc_self ]

        if isinstance(other,Geometry):
           lc_other = other.to_cart()
           lq = [ y for (x,y) in lc_other ]
	elif isinstance(other,basestring):
	   # other is a string of xyz file, we parse and build coordinates
           l = other.splitlines()
           assert (len(l)==5)
           l1 = l[2].split()
           l2 = l[3].split()
           l3 = l[4].split()
           assert (l1[0] == Geometry.atom1)
           assert (l2[0] == Geometry.atom2)
           assert (l3[0] == Geometry.atom3)
           assert (math.fabs(float(l1[1])) < 1.0e-14)
           assert (math.fabs(float(l2[1])) < 1.0e-14)
           assert (math.fabs(float(l3[1])) < 1.0e-14)
           lq = [ (float(l1[2]),float(l1[3])), (float(l2[2]),float(l2[3])), (float(l3[2]),float(l3[3])) ]
	else:
	   # it is a list of the same type as lp
           lq = [ y for (x,y) in other ]
        return kabsch.calc_rmsd(lp,lq)

    def to_xyzstr(self):

        """ return string of xyz file for this geometry
            NOTE: xyz coordinates will be in angstroms.  """

        # obtain jacobi coordinates and prepare a compact string representing it
	r,R,gam = self.to_jacobi()

	# convert r,R to angstroms and angles to degrees for easy understanding.
	r = misc.ToAngs(r)
	R = misc.ToAngs(R)
	gam = misc.ToDeg(gam)

	sr = misc.strip_float("{0:9.6f} ang".format(r))
	sR = misc.strip_float("{0:9.6f} ang".format(R))
	sg = misc.strip_float("{0:7.3f} deg".format(gam))

        # number of atoms on first line and title on second line

	s = "   3" + "\n"
	s += "(rho,theta,phi) = " + str(self) + "  "
	s += "(r,R,gam) = " + "(" + sr.strip() + "," + sR.strip() + "," + sg.strip() + ")" + "\n"

	# cartesian coords
	lc =  self.to_cart()
	at1,(x1,y1) = lc[0] ; x1 = misc.ToAngs(x1) ; y1 = misc.ToAngs(y1)
	at2,(x2,y2) = lc[1] ; x2 = misc.ToAngs(x2) ; y2 = misc.ToAngs(y2)
        at3,(x3,y3) = lc[2] ; x3 = misc.ToAngs(x3) ; y3 = misc.ToAngs(y3)

	s += "{0:2s}{1:22.10f}{2:20.10f}{3:20.10f}".format(" " + at1,0.0,x1,y1) + "\n"
	s += "{0:2s}{1:22.10f}{2:20.10f}{3:20.10f}".format(" " + at2,0.0,x2,y2) + "\n"
	s += "{0:2s}{1:22.10f}{2:20.10f}{3:20.10f}".format(" " + at3,0.0,x3,y3) + "\n"

	return s

    def IsLinear(self):
	if math.fabs(self.theta-math.pi/2) < 1.0e-10:
	   return True
	else:
	   return False


