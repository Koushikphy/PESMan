import misc
import math

class Geometry():
    """A class storing a geometry in polar coordinates"""

    # atomic names and masses of atoms in a dodecatomic molecule.
    # WARN : These are class variables shared by all instances. Do not change them.
    # TODO : Make them immutable
    atom1, mass1 = "N", 14.006700
    atom2, mass2 = "O", 15.999400
    atom3, mass3 = "O", 15.999400

    def __init__(self, id=0):
       """ constructor with polar coords
      #      NOTE: by default radians
      #      set degs = True for degrees """
      #  self.rho = rho
      #  self.phi = phi
      #  if degs:
      #     self.phi = misc.ToRad(self.phi)
      #  # also set id, useful for later manipulations
       self.id = id


    def createXYZfile(self, geomRow, filename='tr'):
       self.rho = geomRow['rho']
       self.phi = geomRow['phi']
       with open(filename, 'w') as f:
          f.write(self.to_xyzstr())

    def __repr__(self):
       """ more exact representation of geometry object """
       return "Geometry({0:10.6f},{1:10.6f})".format(self.rho,self.phi)

    def __str__(self):
       """ readable representation of geometry object """
       srho = "{0:7.3f}".format(self.rho)
       sphi = "{0:7.3f} deg".format(misc.ToDeg(self.phi))
       srho = misc.strip_float(srho)
       sphi = misc.strip_float(sphi)
       sid = ""
       if self.id:
          sid = "geom-" + '{:05d}'.format(self.id)
          sid = "geom-" + str(self.id)
       return sid + "-(" + srho + "," + sphi + ")"

    def filestr(self):
       """ a representation of geometry object suitable for use as file name """
       srho = "{0:7.3f}".format(self.rho)
       sphi = "{0:7.3f}".format(misc.ToDeg(self.phi))
       srho = misc.strip_float(srho)
       sphi = misc.strip_float(sphi)
       sid = ""
       if self.id:
          sid = "geom-" + '{:05d}'.format(self.id)
          sid = "geom" + str(self.id)
       return sid + "-" + srho + "-" + sphi

    def to_polar(self):
        """ return a tuple containing polar coords """
        return (self.rho,self.phi)

    def to_cart(self):
        """ Convert to cartesian coordinates
            NOTE : coordinates will be in angstroms """


#       ang = 0.529177
        hcross = 0.063508
        cminvtinv = 0.001883651
        nmass = Geometry.mass1
        omass = Geometry.mass2

        omega1 = 759.61*cminvtinv         
        omega2 = 1353.31*cminvtinv         
        omega3 = 1687.70*cminvtinv         
         
	x01= -0.0000000000 
	y01=  0.0073802030        
	z01=  0.0000000000
	x02=  1.1045635392        
	y02=  0.4739443250        
	z02=  0.0000000000
	x03= -1.1045635392        
	y03=  0.4739443250        
	z03=  0.0000000000
 
        rho = self.rho
        phi = self.phi
 
        Q1 = rho*math.cos(phi)
        Q3 = rho*math.sin(phi)
        Q2 = 0.0
        
	x1= math.sqrt(hcross/nmass)*( 0.0000000*Q1/math.sqrt(omega1)  +  0.0000000*Q2/math.sqrt(omega2)    +    0.8122235*Q3/math.sqrt(omega3))
	y1= math.sqrt(hcross/nmass)*( 0.6167049*Q1/math.sqrt(omega1)  +  0.5614428*Q2/math.sqrt(omega2)    +    0.0000000*Q3/math.sqrt(omega3))
	z1= math.sqrt(hcross/nmass)*( 0.0000000*Q1/math.sqrt(omega1)  +  0.0000000*Q2/math.sqrt(omega2)    +    0.0000000*Q3/math.sqrt(omega3))
	x2= math.sqrt(hcross/omass)*( 0.4760237*Q1/math.sqrt(omega1)  -  0.5228780*Q2/math.sqrt(omega2)    -    0.3799808*Q3/math.sqrt(omega3))
	y2= math.sqrt(hcross/omass)*(-0.2885117*Q1/math.sqrt(omega1)  -  0.2626586*Q2/math.sqrt(omega2)    -    0.1605027*Q3/math.sqrt(omega3))
	z2= math.sqrt(hcross/omass)*( 0.0000000*Q1/math.sqrt(omega1)  +  0.0000000*Q2/math.sqrt(omega2)    +    0.0000000*Q3/math.sqrt(omega3))
	x3= math.sqrt(hcross/omass)*(-0.4760237*Q1/math.sqrt(omega1)  +  0.5228780*Q2/math.sqrt(omega2)    -    0.3799808*Q3/math.sqrt(omega3))
	y3= math.sqrt(hcross/omass)*(-0.2885117*Q1/math.sqrt(omega1)  -  0.2626586*Q2/math.sqrt(omega2)    +    0.1605027*Q3/math.sqrt(omega3))
	z3= math.sqrt(hcross/omass)*( 0.0000000*Q1/math.sqrt(omega1)  +  0.0000000*Q2/math.sqrt(omega2)    +    0.0000000*Q3/math.sqrt(omega3))
           
        n1x,n1y,n1z = x1 + x01, y1 + y01,z1 + z01
        o2x,o2y,o2z = x2 + x02, y2 + y02,z2 + z02
        o3x,o3y,o3z = x3 + x03, y3 + y03,z3 + z03
 
        lcart = [ (Geometry.atom1,(n1x,n1y,n1z)), (Geometry.atom2,(o2x,o2y,o2z)), (Geometry.atom3,(o3x,o3y,o3z))]
 
        return lcart

    def distance(self,other):
        """ return metric distance from the other geometry. """

        rh_self,ph_self = self.to_polar() 

        if isinstance(other,Geometry):
           rh_other,ph_other = other.to_polar() 
        else:
           raise Exception("Error in calculating geometry dist. One of the arguments is not a class object")
           
        x1 = rh_self*math.cos(ph_self)
        y1 = rh_self*math.sin(ph_self)
        
        x2 = rh_other*math.cos(ph_other)
        y2 = rh_other*math.sin(ph_other)

        dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        
        return dist

    def to_xyzstr(self):

        """ return string of xyz file for this geometry
            NOTE: xyz coordinates will be in angstroms.  """

        # number of atoms on first line and title on second line

	s = "   3" + "\n"
	s += "(rho,phi) = " + str(self) + "  \n"

	# cartesian coords
	lc =  self.to_cart()
	at1,(x1,y1,z1) = lc[0]
	at2,(x2,y2,z2) = lc[1]
        at3,(x3,y3,z3) = lc[2]

	s += "{0:2s}{1:22.10f}{2:20.10f}{3:20.10f}".format(" " + at1,x1,y1,z1) + "\n"
	s += "{0:2s}{1:22.10f}{2:20.10f}{3:20.10f}".format(" " + at2,x2,y2,z2) + "\n"
	s += "{0:2s}{1:22.10f}{2:20.10f}{3:20.10f}".format(" " + at3,x3,y3,z3) + "\n"

	return s





geomObj = Geometry()
