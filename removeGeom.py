import numpy as np 
import shutil
import tarfile
import os
import glob 
from multiprocessing import Pool


def removeWfuFromArchieve(geom):

    # path to this geom archieve, hardcoded for simplicity, change according to use
    path = 'GeomData/geom%d/multi1.tar.bz2'%geom  

    if not os.path.exists(path) :
        print("File %s doesn't exists. You may haven't archived yet"%path)
        return

    dPath = path.strip('.tar.bz2').strip('/')  # directory path to extract

    # unarchived directory exists
    if os.path.exists(dPath):
        print("Folder %s exists, this should not have happened. Check this geom."%dPath)
        return

    os.makedirs(dPath)

    def nowfu(mem): # extract everything except for the wfu file
        for t in mem:
            if not t.name.endswith('wfu'):
                yield t 

    with tarfile.open(path) as tar: #  extract the file in that directory
        for i in tar.getnames(): # check if the archive contains archive file
            if i.endswith('wfu') : 
                break
        else:
            print('No wfu file found for %s'%path)
            return
        tar.extractall(path=dPath, members=nowfu(tar))

    os.remove(path) # delete older archive

    shutil.make_archive(dPath, 'bztar', root_dir=dPath, base_dir='./')   # create new archieve
    shutil.rmtree(dPath)        # remove extracted directory
    print('wfu successfully removed from %s'%path)



# sample the geomdatas to delete
data = np.loadtxt('./geomdata.txt')
data = np.array(data, dtype=np.int)

ind = data[:,3]%3==0  # keep phi divisible by 3

ind[:2] = False # also keep the first two geometries as they are 0 phi (0,0),(1,0), just such

indToDelete = data[~ind][:,0] # these geomids will be deleted

# delete them in parallel
p = Pool(4)
p.map(removeWfuFromArchieve, indToDelete[:10])