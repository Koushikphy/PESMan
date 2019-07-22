import misc
import math
import kabsch

def jac2cart(rs,rc,gamma,atom1,atom2,atom3):
   """ Convert to cartesian coordinates in yz plane.
       Molecule will be on yz plane with m2 and m3 lying on z-axis.
       NOTE : coordinates will be in atomic units NOT angstroms """
   f1y = rc*math.sin(gamma)
   f1z = rc*math.cos(gamma)
   h2y = 0.0
   h2z = -rs/2.0
   h3y = 0.0
   h3z = rs/2.0
   lcart = [ (atom1,(f1y,f1z)), (atom2,(h2y,h2z)), (atom3,(h3y,h3z)) ]
   return lcart

class Geometry():
    """A class storing a geometry in hyper-spherical coordinates"""

    # atomic names and masses of atoms in a triatomic molecule.
    # WARN : These are class variables shared by all instances. Do not change them.
    # TODO : Make them immutable
    atom1, mass1 = "F", 19.0
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

	M = m1 + m2 + m3
	mu = math.sqrt(m1*m2*m3/M)
	d1 = math.sqrt(m1*(m2+m3)/(mu*M))
	d2 = math.sqrt(m2*(m3+m1)/(mu*M))
	d3 = math.sqrt(m3*(m1+m2)/(mu*M))
	eps3 = 2 * math.atan(m2/mu)
	eps2 = 2 * math.atan(m3/mu)
	R1 = (1.0/math.sqrt(2.0))*rho*d3*math.sqrt(1.0+math.sin(theta)*math.cos(phi+eps3)) # F-H2 distance
	R2 = (1.0/math.sqrt(2.0))*rho*d1*math.sqrt(1.0+math.sin(theta)*math.cos(phi))      # H1-H2 distance
	R3 = (1.0/math.sqrt(2.0))*rho*d2*math.sqrt(1.0+math.sin(theta)*math.cos(phi-eps2)) # F-H1 distance
	if R1 < 1e-10:
	   R1 = 0.0
	if R2 < 1e-10:
	   R2 = 0.0
	if R3 < 1e-10:
	   R3 = 0.0

        area = misc.AreaTriangle(R1,R2,R3)
	x = R2*R2 + R3*R3 - R1*R1
	y = 4.0*area
	Ang123 = math.atan2(y,x) 
	x2 = (0.0,0.0)
        x3 = (R2,0.0) 
        x1 = (R3*math.cos(Ang123),R3*math.sin(Ang123))
 	# these are non-mass scaled jacobi coords
        # r : (x3-x2)
        # R : x1 - com(x3,x2)
        # gamma : angle between r and R
        r = (R2,0.0)
        R = (R3*math.cos(Ang123) - m3*R2/(m2+m3) , R3*math.sin(Ang123))
        rs = math.sqrt(misc.dotp(r,r))
        rc = math.sqrt(misc.dotp(R,R))
	if rc < 1e-10:
	   rc = 0.0
	
        rtil = (R2*m2/(m2+m3),0.0)
        drtil = math.sqrt(misc.dotp(rtil,rtil))
        Areasmall = misc.AreaTriangle(drtil,R1,rc)
        y = 4.0 * Areasmall
	x = drtil*drtil + rc*rc - R1*R1
	if math.fabs(x) < 1e-10:
	   x = 0.0
	gamma = math.atan2(y,x)

        # we assert that gamma is always less than 90 degree always - our grid does not produce this for H2F
        # assert (gamma <= math.pi/2)

	return (rs, rc, gamma)

    def to_cart(self):
        """ Convert to cartesian coordinates in yz plane.
            Molecule will be on yz plane with m2 and m3 lying on z-axis.
            NOTE : coordinates will be in atomic units NOT angstroms """

        rs,rc,gamma = self.to_jacobi()
	#f1y = rc*math.sin(gamma)
	#f1z = rc*math.cos(gamma)
	#h2y = 0.0
	#h2z = -rs/2.0
	#h3y = 0.0
	#h3z = rs/2.0
	#lcart = [ (Geometry.atom1,(f1y,f1z)), (Geometry.atom2,(h2y,h2z)), (Geometry.atom3,(h3y,h3z)) ]
	return jac2cart(rs,rc,gamma,Geometry.atom1,Geometry.atom2,Geometry.atom3)

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


