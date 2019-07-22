import math
import misc
import geometry

def GenerateGrid(lrho,lphi):
    """ Generate a grid of geometries in polar coordinates
        a list of geometry class objects are returned.
        lrho/lphi : list of values """
    lhs = []
    for rho in lrho:
      for phi in lphi:
         pc = geometry.Geometry(rho,phi)
         lhs.append(pc)
    return lhs

def geomsave(prefix,lg):
    for g in lg:
       gname = g.filestr()
       s = g.to_xyzstr()
       fname = prefix + "-" + gname + ".xyz"
       f = open(fname, 'w')
       f.write(s)
       f.close()

if __name__ == "__main__":

    pass
#   import math
#   pi = math.pi

#   lrho = [(1.5 + i) for i in range(10)]
#   lthe = [0.0 + i*5.0*pi/180.0 for i in range(19)]
#   lphi = [0.0 + i*5.0*pi/180.0 for i in range(37)]

#   lgeom = GenerateHSGrid(lrho,lthe,lphi)
#   #for g in lgeom:
#   #    print g.to_xyzstr(),

#   #
#   #ljac = [ hyper2jacobi(rho,the,phi,m1,m2,m3) for (rho,the,phi) in lhs ]
#   #lgeom = zip(lhs,ljac)

#   lpath = [ g for g in lgeom if IsPath(g) ]
#   llinear = [ g for g in lgeom if g.IsLinear() and not IsPath(g) ]
#   lnormal = [ g for g in lgeom if (g not in lpath) and (g not in llinear) ]

#   # write out each geometry
#   geomsave("p",lpath)
#   geomsave("l",llinear)
#   geomsave("g",lnormal)

