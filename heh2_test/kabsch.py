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
    v, _, w = np.linalg.svd(c)
    if (np.linalg.det(v) * np.linalg.det(w)) < 0.0 : w[-1] = -w[-1]
    r= np.dot(v, w)
    p = np.dot(p, r)
    return np.sqrt(np.sum((p-q)**2)/p.shape[0])


print calc_rmsd1(p,q)
print calc_rmsd(p,q)