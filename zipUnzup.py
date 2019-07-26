
def zipAll():
    for path,_,_ in os.walk('.'):
        if 'multi' in path or 'mrci' in path:
            shutil.make_archive(path, 'bztar', root_dir=path, base_dir='./')
            shutil.rmtree(path)



def unzipAll():
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.tar.bz2'):
                file = os.path.join(root,file)
                path = file.replace('.tar.bz2', '')
                shutil.unpack_archive(file, extract_dir=path)
                os.remove(file)