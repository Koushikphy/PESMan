import numpy as np
p =np.array([ [-1., 0., 0.],[ 0., 0., 0.],[ 0., 1., 0.],[ 0., 1., 1]])
q =np.array([ [0., -1, -1],[ 0., -1, 0.],[ 0., 0, 0.],[ -1, 0, 0]])



def kabsch(p, q):
    c = np.dot(np.transpose(p), q)
    v, s, w = np.linalg.svd(c)
    d = (np.linalg.det(v) * np.linalg.det(w))<0.0
    if d :
        s[-1] = -s[-1]
        v[:, -1] = -v[:, -1]
    # create rotation matrix u
    return  np.dot(v, w)

def rmsd(V, W):

    D = len(V[0])
    N = len(V)
    result = 0.0
    for v, w in zip(V, W):
        result += sum([(v[i] - w[i])**2.0 for i in range(D)])
    return np.sqrt(result/N)


def calc_rmsd(p,q):
    p -= sum(p)/len(p) #np.mean(p, axis=0)
    q -= sum(q)/len(q) #np.mean(q, axis=0)
    p = np.dot(p, kabsch(p, q))
    return rmsd(p,q)


def calc_rmsd1(p,q):
    p -= np.mean(p, axis=0)
    q -= np.mean(q, axis=0)
    c = np.dot(np.transpose(p), q)
    v, s, w = np.linalg.svd(c)
    if (np.linalg.det(v) * np.linalg.det(w)) < 0.0 : w[-1] = -w[-1]
    r= np.dot(v, w)
    p = np.dot(p, r)
    
    return np.sqrt(np.sum((p-q)**2)/p.shape[0])


def calc_rmsd2(p,q):
    p -= np.mean(p, axis=0)
    q -= np.mean(q, axis=0)
    e0 = np.sum(np.square([p,q]))
    c = np.dot(np.transpose(p), q)
    v, s, w = np.linalg.svd(c)
    return np.sqrt(np.abs((e0 - 2.0*np.sum(s))/p.shape[0]))
    






def numpy_svd_rmsd_rot(p, q):
    """
    Returns rmsd and optional rotation between 2 sets of [nx3] arrays.
    
    This requires numpy for svd decomposition.
    The transform direction: transform(m, ref_crd) => target_crd.
    """
    
    # p -= np.mean(p, axis=0)
    # q -= np.mean(q, axis=0)
    
    n_vec = np.shape(p)[0]
    correlation_matrix = np.dot(np.transpose(p), q)
    v, s, w = np.linalg.svd(correlation_matrix)
    is_reflection = (np.linalg.det(v) * np.linalg.det(w)) < 0.0
    
    if is_reflection:
        s[-1] = - s[-1]
    E0 = np.sum(np.square([p,q]))

    rmsd_sq = (E0 - 2.0*sum(s)) / float(n_vec)
    rmsd_sq = max([rmsd_sq, 0.0])
    rmsd = np.sqrt(rmsd_sq)
    
    if is_reflection:
        v[-1,:] = -v[-1,:]
    rot33 = np.dot(v, w)
    # m = v3.identity()
    # m[:3,:3] = rot33.transpose()
    
    return rmsd


print calc_rmsd1(p,q)
print calc_rmsd(p,q)
print numpy_svd_rmsd_rot(p,q)
print calc_rmsd2(p,q)