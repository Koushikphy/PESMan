import math
import misc
import kabsch
import geometry

def GenerateHSGrid(lrho,ltheta,lphi):
    """ Generate a grid of geometries in hyperspherical coordinates
        a list of geometry class objects are returned.
        lrho/ltheta/lphi : list of values """
    lhs = []
    for rho in lrho:
      for theta in ltheta:
        for phi in lphi:
           hc = geometry.Geometry(rho,theta,phi)
           lhs.append(hc)
    return lhs

def IsPath(geom):
    """ Decide if a geometry is pathlogical one. It will be used to tag the geometry.
        NOTE : This is not a class function, but a general function.
        TODO : Is there a way to decide based on nuclear repulsion energy? """
    lcart = geom.to_cart()
    atom1,(f1y,f1z) = lcart[0]
    atom2,(h2y,h2z) = lcart[1]
    atom3,(h3y,h3z) = lcart[2]
    Rhf1 = math.sqrt((f1y-h2y)**2+(f1z-h2z)**2)
    Rhf2 = math.sqrt((f1y-h3y)**2+(f1z-h3z)**2)
    Rhh  = math.sqrt((h2y-h3y)**2+(h2z-h3z)**2)
    val = False
    if min(Rhf1,Rhf2) < misc.ToBohrs(0.6):
      val = True
    if Rhh < misc.ToBohrs(0.6):
      val = True
    return val

def islinear_channel(geom):
    """ Decide whether a linear geometry is in the entrance or exit channel"""
    lcart = geom.to_cart()
    atom1,(f1y,f1z) = lcart[0]
    atom2,(h2y,h2z) = lcart[1]
    atom3,(h3y,h3z) = lcart[2]
    Rhf1 = math.sqrt((f1y-h2y)**2+(f1z-h2z)**2)
    Rhf2 = math.sqrt((f1y-h3y)**2+(f1z-h3z)**2)
    Rhh  = math.sqrt((h2y-h3y)**2+(h2z-h3z)**2)
    if math.fabs(Rhf1 + Rhf2 - Rhh) < 1.0e-10:
       return True  # Exit Channel (H-F-H)
    else:
       return False # Entrance channel (H-H-F)

def geom_tags(g):
   """ generate tags for geometry """
   l = []
   if g.IsLinear():
      l.append("linear")
      if islinear_channel(g):
         l.append("Finside")
      else:
         l.append("Foutside")
   if IsPath(g):
      l.append("path")
   return ":".join(l)
   
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

