#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import numpy

def getcom(mr1,mr2,mr3):
    # return com
    m1,(x1,y1) = mr1
    m2,(x2,y2) = mr2
    m3,(x3,y3) = mr3
    mt = m1 + m2 + m3
    xcom = ((m1 * x1 + m2 * x2 + m3 * x3)/mt)
    ycom = ((m1 * y1 + m2 * y2 + m3 * y3)/mt)
    return xcom, ycom 
                        
def relcom(mr1,mr2,mr3):
    # return coordinates relative to com
    m1,(x1,y1) = mr1
    m2,(x2,y2) = mr2
    m3,(x3,y3) = mr3
    xcom,ycom = getcom(mr1,mr2,mr3)
    mrel1 = (m1,((x1-xcom),(y1-ycom)))
    mrel2 = (m2,((x2-xcom),(y2-ycom)))
    mrel3 = (m3,((x3-xcom),(y3-ycom)))
    return mrel1, mrel2, mrel3 
                        
def getmjoc(mr1,mr2,mr3):
    # returns the mass scaled jocobi coordinates relative to mr1
    # see Johnson's paper
    # r1 = inv(d1)*(x3-x2)
    # R1 = d1*(x1-com(x3,x2))
    # mr1,mr2,mr3 are here considered as coordinates relative to com although this is not really necessary
    m1,(x1,y1) = mr1
    m2,(x2,y2) = mr2
    m3,(x3,y3) = mr3

    mt = m1 + m2 + m3
    mu = (math.sqrt(m1*m2*m3/mt))
    mu123 = (m1*(m2+m3)/mt)
    
    d1 = math.sqrt(mu123/mu)
    
    r1x = (x3-x2)/d1
    r1y = (y3-y2)/d1
    R1x = (d1*(x1-(m2*x2+m3*x3)/(m2+m3)))
    R1y = (d1*(y1-(m2*y2+m3*y3)/(m2+m3)))
    
    return (r1x,r1y),(R1x,R1y) 
                        
def dotp(p1,p2):
    x1,y1 = p1[0],p1[1]
    x2,y2 = p2[0],p2[1]
    return x1*x2 + y1*y2 
                        
def crosp(p1,p2):
    x1,y1 = p1[0],p1[1]
    x2,y2 = p2[0],p2[1]
    return x1*y2 - x2*y1 
                        
def hsrad(r1,R1):
    rx,ry = r1[0],r1[1]
    Rx,Ry = R1[0],R1[1]
    return math.sqrt(rx*rx+ry*ry+Rx*Rx+Ry*Ry) 
                        
def moiner(mr1,mr2,mr3):
    #return moment of inertia matrix
    #co-ordinates are assumed to be w.r.t com
    m1,(x1,y1) = mr1
    m2,(x2,y2) = mr2
    m3,(x3,y3) = mr3
    Ixx0 = m1*y1^2 + m2*y2^2 + m3*y3^2
    Iyy0 = m1*x1^2 + m2*x2^2 + m3*x3^2
    Ixy0 = m1*x1*y1 + m2*x2*y2 + m3*x3*y3 # wrong sign, does it matter? eigenvalues are unaltered
    # Imat = matrix(RR,[[Ixx0,Ixy0],[Ixy0,Iyy0]])
    # use numpy arrays in place of sage matrix class
    Imat = numpy.array([[Ixx0, Ixy0], [Ixy0, Iyy0]], dtype=float)
    return Imat 
                        
                        
def transpa(mr1,mr2,mr3):
    """ Transform to principle axes system """
    # the triatomic molecule is assumed to be in x-y plane
    # input: coordinates with respect to the com
    # output: coordinates with respect to principle axes of inertia
    # if necessary, the coordinate axes is reoriented such that z-axis conincides with A = (r1 X R1)
    # A is not only kinematic invariant, but also independent of particle masses
    m1,(x1,y1) = mr1
    m2,(x2,y2) = mr2
    m3,(x3,y3) = mr3
    r1,R1 = getmjoc((m1,(x1,y1)),(m2,(x2,y2)),(m3,(x3,y3)))
    A = crosp(r1,R1)
    if A < 0:
        #flip x and z coordinates (amounts to rotating along y axis by 180)
        x1 = -x1
        x2 = -x2
        x3 = -x3
        # nothing to flip for z, they are all zero
    # if input coordinates are with respect to com, com needed be checked again
    r1,R1 = getmjoc((m1,(x1,y1)),(m2,(x2,y2)),(m3,(x3,y3)))
    A = crosp(r1,R1)
    # now A must be positive
    # obtain principle moments and axes of inertia
    # construct moment of inertial matrix with respect to com
    Ixx0 = m1*(y1**2) + m2*(y2**2) + m3*(y3**2)
    Iyy0 = m1*(x1**2) + m2*(x2**2) + m3*(x3**2)
    Ixy0 = m1*x1*y1 + m2*x2*y2 + m3*x3*y3 # wrong sign, does it matter?
    Imat = numpy.array([[Ixx0, Ixy0], [Ixy0, Iyy0]], dtype=float)
    #print "In TransPA "
    #print Imat
    # obtain eigen vectors and eigen values
    eigval,eigvec = numpy.linalg.eigh(Imat)
    #print eigval[0],eigvec[:,0]
    #print eigval[1],eigvec[:,1]
    # define principle moments of inertia
    # numpy eigen solver returns in ascending order
    Ixx = eigval[0]
    xvec = eigvec[:,0]
    Iyy = eigval[1]
    yvec = eigvec[:,1]
    if Ixx > Iyy:
        assert(0) # this should not happen though, numpy returns in ascending order
        Ixx,Iyy = Iyy,Ixx
        xvec,yvec = yvec,xvec
    # alter sign of eigenvector corresponding to Ixx so that their y component is positive
    if xvec[1] < 0:
        xvec = numpy.array([-xvec[0],-xvec[1]])
    # x and y direction is defined as per Ixx < Iyy convention
    # now choose yvec s.t x,y,z forms right handed coordinate system
    # use cmp to get sign of a number
    sgn = cmp(crosp(xvec,yvec),0.0)
    if sgn < 0:
        yvec = numpy.array([-yvec[0],-yvec[1]])
    # now find the angle of rotation
    nx = math.sqrt(dotp(xvec,xvec))
    dp = dotp(xvec,numpy.array([1.0,0.0]))
    alpha = math.acos(dp/nx)
    #print "alpha (deg) = ", alpha*180.0/math.pi
    # setup rotation matrix
    # convert to numpy array
    # Mrot = matrix(RR,[[math.cos(alpha),-math.sin(alpha)],[math.sin(alpha),math.cos(alpha)]])
    Mrot = numpy.array([[math.cos(alpha),-math.sin(alpha)],[math.sin(alpha),math.cos(alpha)]],dtype=float)
    # rotate the coordinates to principle axes
    pnew = numpy.dot(Mrot,numpy.array([x1,y1],dtype=float))
    p1new = (pnew[0],pnew[1])
    pnew = numpy.dot(Mrot,numpy.array([x2,y2],dtype=float))
    p2new = (pnew[0],pnew[1])
    pnew = numpy.dot(Mrot,numpy.array([x3,y3],dtype=float))
    p3new = (pnew[0],pnew[1])
    mr1new = (m1,p1new)
    mr2new = (m2,p2new)
    mr3new = (m3,p3new)
    #print "Ret TransPA "
    return mr1new, mr2new, mr3new 
                        
def getrs(rho,theta,phi):
    # convert unmodified hs coords to r_k and R_k
    # see Johnsons paper for definitions
    # WARNING: rho,theta,phi are not the final modified coordinates, but initial unmodified ones given in Eq (28)
    rx = rho*math.cos(theta)*math.cos(phi)
    ry = -rho*math.sin(theta)*math.sin(phi)
    Rx = rho*math.cos(theta)*math.sin(phi)
    Ry = rho*math.sin(theta)*math.cos(phi)
    return (rx,ry),(Rx,Ry) 
                        
def tohyper(mr1,mr2,mr3):
    # convert to hyperspherical coordinates
    # input: mri = (m_i,(x_i,y_i)) - mass and x,y coordinates of triatomic molecule
    # see Johnson's paper for details
    # the coordinate axes if needed is oriented such that z-axis conincides with A = 1/2 (r1 X R1)
    # A is not only a kinematic invariant, but also independent of particle masses
    # hyper-radius rho is a kinematic invarient, but depends on relative masses
    # if all masses are same, then we should get same coordinates
    
    # first convert to co-ordinates relative to com
    (mrel1,mrel2,mrel3) = relcom(mr1,mr2,mr3)

    # convert to principle axes coordinates
    (mr1new, mr2new, mr3new) = transpa(mrel1,mrel2,mrel3)

    # now convert to hypersphreical
    m1,(x1,y1) = mr1new
    m2,(x2,y2) = mr2new
    m3,(x3,y3) = mr3new
    r1,R1 = getmjoc(mr1new,mr2new,mr3new)
    A = (1.0/2.0)* crosp(r1,R1)
    assert (A >= 0.0)
    #print "A = ",A

    r1x,r1y = r1
    R1x,R1y = R1
    # hyper-radius -- eq (14) and eq (29)
    rho2 = r1x**2 + r1y**2 + R1x**2 + R1y**2
    rho = math.sqrt(rho2)
    # hyper-angle 0 <= Theta <= math.pi/4
    # Sin(2 Theta) = 4A / rho^2
    # Cos(2 Theta) = Q / rho^2
    # A is already computed, compute Q
    Q = r1x**2 + R1x**2 - r1y**2 - R1y**2 # this is only valid in principle axes coordinates -- see unnamed eq following (31) 
    #print "Q=",Q # this must be greater than or equal to zero
    if Q < 0.0:
        # small values can be set to zero
        if math.fabs(Q) < 1.0e-14:
            Q = 0.0
    assert(Q >= 0.0)
    #print "t=",r1x*r1y + R1x*R1y # this must be zero in principle axes coordinates -- eqn
    assert(math.fabs(r1x*r1y + R1x*R1y) < 1.0e-5)
    try:
        theta = (1.0/2.0)*math.atan2(4.0*A,Q)
    except RuntimeError:
        theta = 0.0
    assert(theta >= 0.0)
    assert(theta <= math.pi/4.0)
    #print "theta =",(theta*180.0/math.pi)
    #print "A = ",((1.0/4.0) * rho**2 * math.sin(2.0*theta))
    #print "Q = ",(rho**2 * math.cos(2.0*theta))

    # hyper-angle phi_1
    # v_1 = 2 dot(r1,R1)
    # u_1 = |r1|^2 - |R1|^2
    # v_k = Q math.sin(2 phi_k)
    # u_k = Q math.cos(2 phi_k)
    v1 = 2.0 * dotp(r1,R1)
    u1 = dotp(r1,r1) - dotp(R1,R1)
    #print "v1,u1 =",(v1),(u1)
    # first find both solutions phi_a and phi_b as in Johnsons paper -- discussions following Eq (37)
    # phi_a is smaller one, phi_b is larger one
    try:
        phi_a = math.atan2(v1,u1)
        #print "pha_a is = ",(phi_a)
    except RuntimeError:
        # any value will do now
        phi_a = 0.0
    #print "phi_a (deg) 1", (phi_a*180.0/math.pi)
    if (phi_a) < 0.0:
        phi_a = phi_a + 2.0*math.pi # correction for third and fourth quadrant -- make sure this is positive
    # by now phi_a always lies between 0  and 2*math.pi
    #print "phi_a (deg) 2", (phi_a*180.0/math.pi)
    assert(phi_a >= 0.0)
    phi_a = (1.0/2.0)*phi_a
    phi_b = phi_a + math.pi
    #print "phi_a (deg)", (phi_a*180.0/math.pi)
    #print "phi_b (deg)", (phi_b*180.0/math.pi)
    # consistency check to choose phi_k which corresponds to correct signs -- see discussions following Eq (37)
    ra,Ra = getrs(rho,theta,phi_a)
    rb,Rb = getrs(rho,theta,phi_b)
    #print "r1=",((r1x),(r1y))
    #print "R1=",((R1x),(R1y))
    #print "ra=",((ra[0]), (ra[1]))
    #print "Ra=", ((Ra[0]),(Ra[1]))
    #print "rb=",((rb[0]), (rb[1]))
    #print "Rb=", ((Rb[0]),(Rb[1]))
    if dotp(ra,r1) > 0.0 and dotp(Ra,R1) > 0.0:
        phi = phi_a
    elif dotp(rb,r1) > 0.0 and dotp(Rb,R1) > 0.0:
        phi = phi_b
    elif math.fabs(dotp(ra,r1)*dotp(Ra,R1)) < 1.0e-14:
        phi = phi_a
    else:
        #print dotp(ra,r1), dotp(Ra,R1)
        #print dotp(rb,r1), dotp(Rb,R1)
        assert(0)
       
    #print "final phi (deg) = ",(phi*180.0/math.pi)
    # now everything must be all right
    # map to Johnsons modified hs coors -- Eq (46) and (47)
    theta = math.pi/2.0 - 2.0*theta
    phi = math.pi/2.0 - 2.0*phi
    if phi < 0.0:
        phi = phi + 2.0*math.pi # avoid negative values
    # once more might be needed
    if phi < 0:
        phi = phi + 2.0*math.pi
    assert (phi >= 0.0)
    # BIJIT: convert the phi in to that of Billing's coordinate
    if phi >= 0.0 and phi <= 90.0*math.pi/180.0:
       phi = 90.0*math.pi/180.0 - phi
    if phi > 90.0*math.pi/180.0 and phi < 2.0*math.pi:
       phi = 450*math.pi/180.0 - phi

    # now print final results
    #print "rho = ",rho
    #print "theta = ",theta*180.0/math.pi
    #print "phi = ",phi*180.0/math.pi
    #print "A = ",((1.0/4.0) * rho**2 * math.cos(theta))
    #print "Q = ",(rho**2 * math.sin(theta))
    #print "v1= ",(rho**2 * math.sin(theta) * math.cos(phi))
    #print "u1= ",(rho**2 * math.sin(theta) * math.sin(phi))
    return rho, theta, phi 
                        
def dist(p1,p2):
    x1,y1 = p1
    x2,y2 = p2
    return math.sqrt( (x1-x2)**2 + (y1-y2)**2 ) 
                        
def distall(mr1,mr2,mr3):
    # print distances
    m1,p1 = mr1
    m2,p2 = mr2
    m3,p3 = mr3
    #print "r12 =", (dist(p1,p2))
    #print "r23 =", (dist(p2,p3))
    #print "r13 =", (dist(p1,p3))
    return 
                        
def disths(mr1,mr2,mr3,rho,theta,phi):
    # print distances from their hyperspherical coordinates
    # make sure the masses are in floating point numbers, otherwise these operations dont work
    m1,(x1,y1) = mr1
    m2,(x2,y2) = mr2
    m3,(x3,y3) = mr3
    mt = m1+m2+m3
    mu = math.sqrt((m1*m2*m3)/mt)
    mu123 = (m1*(m2+m3))/mt
    mu231 = (m2*(m3+m1))/mt
    mu312 = (m3*(m1+m2))/mt    
    d1 = math.sqrt(mu123/mu)
    d2 = math.sqrt(mu231/mu)
    d3 = math.sqrt(mu312/mu)
    #print d1,d2,d3
    d21 = (d3*rho/math.sqrt(2.0))*math.sqrt( 1.0 + math.sin(theta)*math.sin(phi + 2*math.atan(m2/mu)) )
    d32 = (d1*rho/math.sqrt(2.0))*math.sqrt( 1.0 + math.sin(theta)*math.sin(phi                  ) )
    d13 = (d2*rho/math.sqrt(2.0))*math.sqrt( 1.0 + math.sin(theta)*math.sin(phi - 2*math.atan(m3/mu)) )
    #print "d21",(d21)
    #print "d32",(d32)
    #print "d13",(d13)
    distall(mr1,mr2,mr3)
    return 

def c2vxyz((r,th)):
    # xyz coordinates of c2v geom with r and th
    p1 = 1.0,(0.0,0.0)
    p2 = 1.0,(float(r),0.0)
    p3 = 1.0,(float(r)*math.cos(th),float(r)*math.sin(th))
    return p1,p2,p3 
        
def jacobixyz(rs,rc,gamm):  # rs is jacobi 'r', rc is jacobi 'R' gamm is jacobi 'gamma'
    # xyz coordinates generated from jacobi coordinates
    p1 = 19.0,(rc*math.cos(gamm),rc*math.sin(gamm))
    p2 = 1.0,( -rs/2.0 , 0.0 )
    p3 = 1.0,( rs/2.0 , 0.0 )
    return p1,p2,p3 
        
def xyz2hyperyz(xyz):
    p1,p2,p3 = xyz
    rho,theta,phi = tohyper(p1,p2,p3)
    return (rho*math.sin(theta)*math.sin(phi),rho*math.cos(theta))

def jac2hyper(rs,rc,gam):
    p1,p2,p3 = jacobixyz(rs,rc,gam)
    return tohyper(p1,p2,p3)

if __name__ == "__main__":

        import math

	angs = 0.529177
        p1,p2,p3 = jacobixyz(8.107132288251494,5.865554443174584,9.427732767824582e-07*math.pi/180.0)
        rho,theta,phi = tohyper(p1,p2,p3)
        print "rho,theta,phi = ",rho,theta,phi
        disths(p1,p2,p3,rho,theta,phi)
        
