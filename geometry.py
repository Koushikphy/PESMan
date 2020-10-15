import numpy as np

hcross    = 0.063508
cminvtinv = 0.001883651
ang       = 0.529177209
bohr2ang  = 0.529177209




class Spectroscopic(object):
    def __init__(self, atoms, masses, freq, aq1, aq2, equigeom):
        # equigeom must be in angstorm
        freq          = np.array(freq)
        self.atoms    = atoms
        self.masses   = np.array(masses)
        self.equigeom = np.array(equigeom)
        self.parseData(freq,aq1,aq2)


    def parseData(self, freq, aq1, aq2):
        aq       = np.column_stack([aq1,aq2]).reshape(len(atoms),3,2)
        msInv    = np.sqrt(1/self.masses)
        frqInv   = np.sqrt(hcross/(freq*cminvtinv))
        self.wfm = np.einsum('ijk,k,i->ijk', aq, frqInv, msInv)


    def getCart(self, rho, phi, deg=False):
        if deg: phi = np.deg2rad(phi)
        qCord = [rho*np.cos(phi), rho*np.sin(phi)]
        return self.equigeom + np.einsum('ijk,k->ij',self.wfm, qCord)

    def createXYZfile(self, geomRow, filename, rad=True):
        # this function is called from impexp during export with geomrow as a dictionary
        rho     = geomRow["rho"]
        phi     = geomRow["phi"]
        gId     = geomRow["Id"]
        curGeom = self.getCart(rho,phi)
        if rad:
            phi = np.rad2deg(phi)
        txt = "{}\nGeometry file for GeomId {} : Rho={}, Phi={}\n".format(len(self.atoms), gId, rho, phi)
        for i,j in zip(self.atoms, curGeom):  txt += "{},{},{},{}\n".format(i, *j)
        with open(filename,"w") as f:  f.write(txt)



class Scattering(object):
    def __init__(self, atoms, masses):
        self.atoms  = atoms
        self.masses = masses


    def getCart(self, rho, theta, phi):
        rs, rc, gamma = self.toJacobi(rho, theta, phi)
        p1 = [0, rc*np.sin(gamma), rc*np.cos(gamma)]
        p2 = [0,0.0, -rs/2.0]
        p3 = [0,0.0, rs/2.0 ]
        return np.array([p1, p2, p3])*bohr2ang


    def createXYZfile(self, geomRow, fileName, ddr=False):
        # theta,phi values are in radian in database
        rho     = geomRow["rho"]
        theta   = geomRow["theta"]
        phi     = geomRow["phi"]
        gId     = geomRow["Id"]
        dth     = np.deg2rad(2)/10.0    #  dtheta is 3 degree
        dphi    = np.deg2rad(3)/10.0    #  dphi is 2 degree


        self.saveGeomFile(gId,rho,theta,phi,fileName)

        if not ddr: return
        # ddr case, the flag is controlled in ImpExp file
        self.saveGeomFile(gId,rho,theta+dth,phi,fileName.replace(".xyz","_pdt.xyz"))
        self.saveGeomFile(gId,rho,theta-dth,phi,fileName.replace(".xyz","_mdt.xyz"))
        self.saveGeomFile(gId,rho,theta,phi+dphi,fileName.replace(".xyz","_pdp.xyz"))
        self.saveGeomFile(gId,rho,theta,phi-dphi,fileName.replace(".xyz","_mdp.xyz"))



    def saveGeomFile(self, gId, rho, theta, phi, fileName):
        curGeom = self.getCart(rho, theta, phi)
        
        # theta, phi values will be written as degree in geometry file
        theta = np.rad2deg(theta)
        phi = np.rad2deg(phi)

        txt = "{}\nGeometry file for GeomId {} : rho={}, theta={}, phi={}\n".format(len(self.atoms), gId, rho, theta, phi)
        for i,j in zip(self.atoms, curGeom):  txt += "{},{:18.15f},{:18.15f},{:18.15f}\n".format(i, *j)
        with open(fileName,"w") as f:  f.write(txt)



    def AreaTriangle(self,a,b,c):
        """ area of a tringle with sides a,b,c """
        ps = (a+b+c)/2.0
        ar = ps*(ps-a)*(ps-b)*(ps-c)
        # negative area due to round off errors set to zero
        if ar < 0.0:
            ar = 0.0
        ar = np.sqrt(ar)
        return ar


    def toJacobi(self,rho, theta,phi):
        #! do this in more short way?
        """  returns jacobi coordinates """
        m1, m2, m3 = self.masses

        M    = m1 + m2 + m3
        mu   = np.sqrt(m1*m2*m3/M)
        d1   = np.sqrt(m1*(m2+m3)/(mu*M))
        d2   = np.sqrt(m2*(m3+m1)/(mu*M))
        d3   = np.sqrt(m3*(m1+m2)/(mu*M))
        eps3 = 2 * np.arctan(m2/mu)
        eps2 = 2 * np.arctan(m3/mu)
        R1   = (1.0/np.sqrt(2.0))*rho*d3*np.sqrt(1.0+ np.sin(theta)*np.cos(phi+eps3))
        R2   = (1.0/np.sqrt(2.0))*rho*d1*np.sqrt(1.0+ np.sin(theta)*np.cos(phi))
        R3   = (1.0/np.sqrt(2.0))*rho*d2*np.sqrt(1.0+ np.sin(theta)*np.cos(phi-eps2))

        if R1 < 1e-10:
            R1 = 0.0
        if R2 < 1e-10:
            R2 = 0.0
        if R3 < 1e-10:
            R3 = 0.0

        area = self.AreaTriangle(R1,R2,R3)
        x = R2*R2 + R3*R3 - R1*R1
        y = 4.0*area
        Ang123 = np.arctan2(y,x)
        # x2 = (0.0,0.0)
        # x3 = (R2,0.0)
        # x1 = (R3*np.cos(Ang123),R3*np.sin(Ang123))
        # these are non-mass scaled jacobi coords
        # r : (x3-x2)
        # R : x1 - com(x3,x2)
        # gamma : angle between r and R
        r = (R2,0.0)
        R = (R3*np.cos(Ang123) - m3*R2/(m2+m3) , R3*np.sin(Ang123))
        rs = np.linalg.norm(r)
        rc = np.linalg.norm(R)
        if rc < 1e-10:
            rc = 0.0

        rtil = (R2*m2/(m2+m3),0.0)
        drtil = np.linalg.norm(rtil)
        Areasmall = self.AreaTriangle(drtil,R1,rc)
        y = 4.0 * Areasmall
        x = drtil*drtil + rc*rc - R1*R1
        if np.fabs(x) < 1e-10:
            x = 0.0
        gamma = np.arctan2(y,x)
        return (rs, rc, gamma)

    def geom_tags(self, geom):
        """ generate tags for geometry """
        rho,theta,phi = geom

        dat = self.getCart(rho,theta,phi)
        # dat -> f,h,h and dat[[1, 2, 0]] -> h,h,f
        # so dists are distances of fh, hh, fh
        tmpdat = dat[[1, 2, 0]] - dat
        dists  = np.linalg.norm(tmpdat,axis=1)

        path    = np.any(dists < (0.5*bohr2ang)) #0.5 bohrs, getCart returns in angstorm
        # channel = np.abs(dists[0] + dists[2] - dists[1]) < 1.0e-10
        linear  = np.allclose(theta,np.pi/2.0)# np.abs(theta) < 1.0e-10

        l = ""
        if linear : l+=' linear'
        if path   : l+=' path'
        return l

        # l = []
        # if linear:   # linear position
        #     l.append("linear")
        #     if channel:
        #         l.append("Heinside")
        #     else:
        #         l.append("Heoutside")
        # if path:
        #     l.append("path")
        # return ":".join(l)



class Jacobi(object):
    def __init__(self, atoms):
        self.atoms = atoms

    def getCart(self, sr, cr, gamma):
        # return in angstrom, provided the inputs are in atomic unit and gamma is in radian
        p1 = [0,0.0,  sr/2.0 ]
        p2 = [0,0.0, -sr/2.0]
        p3 = [0, cr*np.sin(gamma), cr*np.cos(gamma)]
        return np.array([p1, p2, p3])*bohr2ang

    def createXYZfile(self, geomRow, filename, rad=True):
        sr = geomRow["sr"]
        cr = geomRow["cr"]
        gamma = geomRow["gamma"]
        gId = geomRow["Id"]
        curGeom = self.getCart(sr, cr, gamma)
        if rad:
            gamma = np.rad2deg(gamma)
        txt = "{}\nGeometry file for GeomId {} : sr={}, cr={}, gamma={}\n".format(len(self.atoms), gId, sr, cr, gamma)
        for i,j in zip(self.atoms, curGeom):  txt += "{},{:13.10f},{:13.10f},{:13.10f}\n".format(i, *j)
        with open(filename,"w") as f:  f.write(txt)

    def geom_tags(self, geom):
        """ generate tags for geometry """
        sr, cr, gamma = geom
        dat = self.getCart(sr, cr, gamma)
        # dat -> h,h,he and dat[[1, 2, 0]] -> h,he,h
        # so dists are distances of hh, hhe, heh
        tmpdat = dat[[1, 2, 0]] - dat
        dists  = np.linalg.norm(tmpdat,axis=1)

        path    = np.any(dists < (0.5*bohr2ang)) #0.5 bohrs, getCart returns in angstorm
        channel = np.abs(dists[1] + dists[2] - dists[0]) < 1.0e-10
        linear  = np.abs(gamma) < 1.0e-10

        l = []
        if linear:   # linear position
            l.append("linear")
            if channel:
                l.append("Heinside")
            else:
                l.append("Heoutside")
        if path:
            l.append("path")
        return ":".join(l)


atoms = ["H","H", "H"]
masses= [1.0,1.0,1.0]
geomObj = Scattering(atoms, masses)
# aq1      = [0.0000000, 0.6167049, 0.0000000, 0.4760237,-0.2885117, 0.0000000,-0.4760237,-0.2885117, 0.0000000]
# aq2      = [0.8122235, 0.0000000, 0.0000000,-0.3799808,-0.1605027, 0.0000000,-0.3799808, 0.1605027, 0.0000000]
# freq     = [759.61,1687.70 ]
# masses   = [14.006700, 15.999400, 15.999400]
# atoms    = ["N", "O", "O"]
# equigeom = [[ -0.0000000000, 0.0073802030,0.0000000000], 
#               [1.1045635392, 0.4739443250, 0.0000000000], 
#               [-1.1045635392, 0.4739443250, 0.0000000000]]

# geomObj = Spectroscopic(atoms, masses, freq, aq1, aq2, equigeom)
