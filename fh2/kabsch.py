"""

Calculate RMSD between two XYZ files

by: Jimmy Charnley Kromann <jimmy@charnley.dk> and Lars Andersen Bratholm <larsbratholm@gmail.com>
project: https://github.com/charnley/rmsd
license: https://github.com/charnley/rmsd/blob/master/LICENSE

Suitably altered to compare any two geometries of planar molecules.
"""

import numpy as np

def kabsch_rmsd(P, Q):
    """
    Rotate matrix P unto Q and calculate the RMSD
    """
    P = rotate(P, Q)
    return rmsd(P, Q)


def rotate(P, Q):
    """
    Rotate matrix P unto matrix Q using Kabsch algorithm
    """
    U = kabsch(P, Q)

    # Rotate P
    P = np.dot(P, U)
    return P


def kabsch(P, Q):
    """
    The optimal rotation matrix U is calculated and then used to rotate matrix
    P unto matrix Q so the minimum root-mean-square deviation (RMSD) can be
    calculated.

    Using the Kabsch algorithm with two sets of paired point P and Q,
    centered around the center-of-mass.
    Each vector set is represented as an NxD matrix, where D is the
    the dimension of the space.

    The algorithm works in three steps:
    - a translation of P and Q
    - the computation of a covariance matrix C
    - computation of the optimal rotation matrix U

    http://en.wikipedia.org/wiki/Kabsch_algorithm

    Parameters:
    P -- (N, number of points)x(D, dimension) matrix
    Q -- (N, number of points)x(D, dimension) matrix

    Returns:
    U -- Rotation matrix

    """

    # Computation of the covariance matrix
    C = np.dot(np.transpose(P), Q)

    # Computation of the optimal rotation matrix
    # This can be done using singular value decomposition (SVD)
    # Getting the sign of the det(V)*(W) to decide
    # whether we need to correct our rotation matrix to ensure a
    # right-handed coordinate system.
    # And finally calculating the optimal rotation matrix U
    # see http://en.wikipedia.org/wiki/Kabsch_algorithm
    V, S, W = np.linalg.svd(C)
    d = (np.linalg.det(V) * np.linalg.det(W)) < 0.0

    if d:
        S[-1] = -S[-1]
        V[:, -1] = -V[:, -1]

    # Create Rotation matrix U
    U = np.dot(V, W)

    return U


def centroid(X):
    """
    Calculate the centroid from a vectorset X
    """
    C = sum(X)/len(X)
    return C


def rmsd(V, W):
    """
    Calculate Root-mean-square deviation from two sets of vectors V and W.
    """
    D = len(V[0])
    N = len(V)
    rmsd = 0.0
    for v, w in zip(V, W):
        rmsd += sum([(v[i]-w[i])**2.0 for i in range(D)])
    return np.sqrt(rmsd/N)


def write_coordinates(atoms, V):
    """
    Print coordinates V
    """
    N, D = V.shape

    print str(N)
    print

    for i in xrange(N):
	if D == 3:
           line = "{0:2s} {1:15.8f} {2:15.8f} {3:15.8f}".format(atoms[i], V[i, 0], V[i, 1], V[i, 2])
	if D == 2:
           line = "{0:2s} {1:15.8f} {2:15.8f}".format(atoms[i], V[i, 0], V[i, 1])
        print line

def get_coordinates_xyz(lyz):
    """
    Prepare yz coordinates to numpy format so that remaining stuff can be callled.
    Input  : a list lyz with (y,z) coordinates for each of the atoms
    Output : coordinates in numpy matrix format
    """
    V = []
    for numbers in lyz:
        if len(numbers) == 2:
            V.append(np.array(numbers))
        else:
            exit("error in input data : " + str(numbers))
    V = np.array(V)
    return V

def calc_rmsd(lp,lq):

    """
    The atoms are assumed to be in yz plane
    input :
       lp,lq are yz coordinate of atoms given as list of (y,z) tuples
       the atoms in each list correspond to each other
    output :
       kabsch rmsd for two geometries
    """
    P = get_coordinates_xyz(lp)
    Q = get_coordinates_xyz(lq)
    Pc = centroid(P)
    Qc = centroid(Q)
    P -= Pc
    Q -= Qc
    krmsd = kabsch_rmsd(P, Q)
    
    return krmsd
