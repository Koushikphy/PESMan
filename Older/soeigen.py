def soeigen(ssomat,sadiapes):
    
    import numpy as np
    from numpy import linalg as LA

    to_au = 4.55633e-6
    adia = [float(i) for i in sadiapes.split()]

    ssomat = ssomat.split()
    somatre = [float(i) for i in ssomat[:len(ssomat)/2]]
    somatim = [complex(0,float(i)) for i in ssomat[len(ssomat)/2:]]

    hso_real = np.zeros((6,6))
    hso_imag = np.full((6,6),complex())
    k = 0
    for i in range(6):
        for j in range(6):
            if i == j:
                hso_real[i][j] = 0.0
            else:
                hso_real[i][j] = somatre[k]
            hso_imag[i][j] = somatim[k]
            k += 1

    hso = hso_real + hso_imag

    uu1 = np.zeros((6,6))
    uu1[0][0],uu1[1][1] = adia[0],adia[1]
    uu1[2][2],uu1[3][3] = adia[0],adia[1]
    uu1[4][4],uu1[5][5] = adia[2],adia[2]

    ham = hso*to_au + uu1
    w1, v = LA.eigh(ham)
    uu2 = np.zeros((6,6))
    uu2[0][0],uu2[1][1] = adia[3],adia[4]
    uu2[2][2],uu2[3][3] = adia[3],adia[4]
    uu2[4][4],uu2[5][5] = adia[5],adia[5]
    
    ham = hso*to_au + uu2
    w2, v = LA.eigh(ham)

    soenr = [w1[0],w1[2],w1[4],w2[0],w2[2],w2[4]]
    txt = " ".join([str(i) for i in soenr])
    return txt



########## Alternate version of the above function written by Koushik #####
# import numpy as np
# from numpy import linalg as lg

# def soeigen(ssomat,sadiapes):

#     to_au = 4.55633e-6
#     adia = map(float, sadiapes.split())

#     hso_real, hso_imag = np.split(np.fromstring(ssomat, sep=' ').reshape(12,6),2)
#     np.fill_diagonal(hso_real,0)
#     hso = hso_real + hso_imag*1j

#     uu1 = np.diag(adia[0:2]*2+adia[2:3]*2)
#     ham = hso*to_au + uu1
#     w1, _ = lg.eigh(ham)

#     uu2 = np.diag(adia[3:5]*2+adia[5:6]*2)
#     ham = hso*to_au + uu2
#     w2, _ = lg.eigh(ham)

#     return ' '.join(np.append(w1[0:5:2],w2[0:5:2]).astype('S1'))
