import os
import shutil
import numpy as np 
# import glob 
# import tarfile
# from multiprocessing import Pool


def removeGeom(geom):

    path = 'GeomData/geom%d'%geom

    if os.path.exists(path):
        shutil.rmtree(path)
        print('Directory %s successfully removed'%path)
    else:
        print("Directory %s doesn't exists"%path)

    # use the below to only delte the wfu from inside the tar file
    # path to this geom archieve, hardcoded for simplicity, change according to use
    # path = 'GeomData/geom%d/multi1.tar.bz2'%geom  

    # if not os.path.exists(path) :
    #     print("File %s doesn't exists. You may haven't archived yet"%path)
    #     return

    # dPath = path.strip('.tar.bz2').strip('/')  # directory path to extract

    # # unarchived directory exists
    # if os.path.exists(dPath):
    #     print("Folder %s exists, this should not have happened. Check this geom."%dPath)
    #     return

    # os.makedirs(dPath)

    # def nowfu(mem): # extract everything except for the wfu file
    #     for t in mem:
    #         if not t.name.endswith('wfu'):
    #             yield t 

    # with tarfile.open(path) as tar: #  extract the file in that directory
    #     for i in tar.getnames(): # check if the archive contains wfu file
    #         if i.endswith('wfu') : 
    #             break
    #     else:
    #         print('No wfu file found for %s'%path)
    #         return
    #     tar.extractall(path=dPath, members=nowfu(tar))

    # os.remove(path) # delete older archive

    # shutil.make_archive(dPath, 'bztar', root_dir=dPath, base_dir='./')   # create new archieve
    # shutil.rmtree(dPath)        # remove extracted directory
    # print('wfu successfully removed from %s'%path)





# sample the geomdatas to delete
data = np.loadtxt('./geomdata.txt')
data = np.array(data, dtype=np.int)

ind = data[:,0]%3==0  # keep geomid divisible by 3

ind[:2] = True # also keep the first two geometries as they are 0 phi (0,0),(1,0), just such

indToDelete = data[~ind][:,0] # these geomids will be deleted

print('Geometries with geomid not divisible by 3 will be deleted except geomid = 0 and 1.')
print('The following %d no of geometries from GeomData will be removed'%len(indToDelete))
print(indToDelete)


try:
    choice = raw_input('Do you want to proceed (y/n)? ')
except NameError:
    choice = input('Do you want to proceed (y/n)? ')


if choice.strip().lower()[0]=='y':
    # delete them in parallel
    # p = Pool(4)
    # p.map(removeGeom, indToDelete)
    for i in indToDelete : removeGeom(i)