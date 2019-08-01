import shutil 
import tarfile
import os


def zipOne(path):
    shutil.make_archive(path, 'bztar', root_dir=path, base_dir='./')
    shutil.rmtree(path)


#TODO: make the extension general
def unZipOne(path, extn = '.tar.bz2'):
    with tarfile.open(path) as tar:
        tar.extractall(path=path.replace(extn,''))
    os.remove(path)


def zipAll(pathList = ['multi','mrci']):
    for path,_,_ in os.walk('.'):
        for subs in pathList:
            if subs in path:
                shutil.make_archive(path, 'bztar', root_dir=path, base_dir='./')
                shutil.rmtree(path)



def unzipAll(base='.', extn = '.tar.bz2'):
    for root, _, files in os.walk(base):
        for file in files:
            if file.endswith('.tar.bz2'):
                file = os.path.join(root,file)
                path = file.replace(extn, '')
                shutil.unpack_archive(file, extract_dir=path)
                os.remove(file)