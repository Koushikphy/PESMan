def parseso(outfile):
 
    import re

    txt = open(outfile).read()
    blocks = re.findall('^ Spin-Orbit Matrix \(CM-1\)(.*?)^ No symmetry adaption',txt,re.DOTALL|re.MULTILINE)
    block = blocks[0]
    data = filter(None,block.split('\n'))[2:]
    dat = [map(float,data[i].split())[4:] for i in [0,2,4,6,8,10]] + [map(float,data[i].split()) for i in [1,3,5,7,9,11]]

    txt =''.join(''.join('{:10.3f}'.format(i) for i in j) for j in dat)
    # for i in range(len(dat)/2):
    #     for j in range(len(dat[i])):
    #         if j>i:
    #             txt += '{:8.2f}'.format(dat[i][j])
    # for i in range(len(dat)/2,len(dat)):
    #     for j in range(len(dat[i])):
    #         if j>i-len(dat):
    #             txt += '{:8.2f}'.format(dat[i][j])

    return txt

