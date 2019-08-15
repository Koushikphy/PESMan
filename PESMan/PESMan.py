#!/usr/bin/env python

import os
import shutil
import tarfile
import argparse
import textwrap
from ImpExp import ImportNearNbrJobs, ExportNearNbrJobs
from ConfigParser import SafeConfigParser


# Takes a folder path compresses it into a '.tar.bz2' file and remove the folder
def zipOne(path):
    print("Archiving %s"%path)
    shutil.make_archive(path, 'bztar', root_dir=path, base_dir='./')
    shutil.rmtree(path)

# Walks through the directory structure recursively finds folder to archive that matches pattern in pathList
def zipAll(subStringList):
    for path,_,_ in os.walk('.'):
        for subs in subStringList:
            if subs in path:
                zipOne(path)


#TODO: make the extension general
# Extracts a compressed file into a folder and removes the file
def unZipOne(path, extn = '.tar.bz2'):
    print("Extracting %s"%path)
    with tarfile.open(path) as tar:
        tar.extractall(path=path.replace(extn,''))
    os.remove(path)

# Walks through the directory structure recursively from `base` and extracts compressed files
def unzipAll(base, extn = '.tar.bz2'):
    for root, _, files in os.walk(base):
        for file in files:
            if file.endswith(extn):
                path = os.path.join(root,file)
                unZipOne(path)


def checkPositive(val):
    val = int(val)
    if val <= 0: raise argparse.ArgumentTypeError("Only positive integers are allowed")
    return val

def notNegetive(val):
    val = int(val)
    if val < 0: raise argparse.ArgumentTypeError("Only positive integers and 0 are allowed")
    return val


parser = argparse.ArgumentParser(
           prog='PESMan',
           formatter_class=argparse.RawTextHelpFormatter,
           description=textwrap.dedent('''\
-----------------------------------------------------
PESMan - a program to manage global PES calculations.
-----------------------------------------------------

This program manages a large number of PES calculations of different type.
The PES data is kept organized in a specified location. The program provides
functionalities required to manipulate this data.
Two key functionalities provided are 'export' and 'import'.

  Export:
    Allows a bunch of calculations to be setup automatically.
    If the calculation depends on a orbital of a previous calculation,
    the wave-function file is automatically copied and input file
    for new calculation is constructed so as to read in the orbital data.
    Different export types/algorithms are available.

  Import:
      Allows a bunch of completed calculations to be checked in.
      After this, this data can be used for subsequent calculations.
      This also allows special manual calculations to be imported.

A database of currently defined calculations, geometry grid, and completed
calculations of a given type is maintained. The PES data is not kept in the
data base. This allows flexibility to externally manipulate the data if needed.
'''),
epilog='BEWARE: A PES is purely an artifact of Born-Oppenheimer separation!!!')


subparsers = parser.add_subparsers(title='Currently implemented sub-commands',dest='subcommand')

parser_export = subparsers.add_parser('export',
                        formatter_class=argparse.RawTextHelpFormatter,
                        description=textwrap.dedent('''\
                        Export calculations of a certain type from the database.
                        A 'gen' type of export uses nearest neigbour algorithm to
                        search for best jobs to be exported, if there is dependency.
                        The data base is modified to reflect the export.
                        The .exp file generated can be used for subsequent import.'''),
                        help='Export calculations of a given type')


parser_export.add_argument('-j', '--jobs', metavar='N', type=checkPositive, default=1, help='Number of jobs to export.\n ')
parser_export.add_argument('--calc-id','-cid', metavar='CID', type=checkPositive, required=True, help='Id of calculation type.\n ')
parser_export.add_argument('--gid-list','-gid', metavar='LGID', nargs='+',  type=checkPositive, default=[], help='List of one or more Gometry Ids.\n ')
parser_export.add_argument('--sid-list','-sid', metavar='LSID', nargs='+', type=notNegetive, default=[], help='List of one or more StartGeom Ids.\n ')
parser_export.add_argument('--depth', '-d', metavar='N', dest='Depth', type=notNegetive, default=1, help='Specify the value of search depth for near neighbour algorithms to find exportable jobs.\nDefault 1\n ')
parser_export.add_argument('--template', metavar='TEMPL', dest='ComTemplate', help='Template file for generating input files.\n ')
parser_export.add_argument('--incl-path',default=False, action='store_true',help='Include pathological geometries.\n ')
parser_export.add_argument('--constraint', metavar='CONST', dest='const', type=str,  help='Specify a database constraint in SQLite3 query format for the geometries to be exported.\n ' )

 
parser_import = subparsers.add_parser('import', description='Import calculations into the PES database.',
                        formatter_class=argparse.RawTextHelpFormatter,
                        help='Import a bunch of completed calculations')

parser_import.add_argument('-e','--exp', metavar='LIST', nargs='+', dest='ExpFile', required=True, help=''' Specify one/multiple export file for import, generated during export.\n ''')
parser_import.add_argument('-ig', metavar="LIST", nargs='+', type=str, default=[],help="List file extensions to ignore during import\n ")
parser_import.add_argument('-del', default=False,dest='delete', action="store_true" ,help="Delete folder after successful import.\n ")
parser_import.add_argument('-zip',default = False, action = "store_true", help = '''Compress the folder during saving in GeomData folder after import. 
This reduces total size and file number substantially. But this is a CPU heavy process 
and compressing and decompressing takes considerable time.''')



parser_zip = subparsers.add_parser('zip', description='Archive one/multiple directory or all individual geom folders.\n ')
parser_zip.add_argument('-d', metavar="LIST", nargs='+', type=str, default=[], help='Provide path(s) of folder(s) to archive.\n ' )
parser_zip.add_argument('-all' ,metavar="DIR", nargs='*', type=str, help='Use this flag to archive all geom folders by default.\nAdditionally provide folder names to to search for to archive.' )

parser_unzip = subparsers.add_parser('unzip', description='Extract one/multiple directory or all individual archived geom folders.\n ')
parser_unzip.add_argument('-f', metavar="LIST", nargs='+', type=str, default=[], help='Provide path(s) of file(s) to unarchive.\n ')
parser_unzip.add_argument('-all' ,metavar="ROOT",nargs='?',const='.', type=str, help='Use this flag to unarchive all geom folders by default.\nAdditionally provide root folder where to search for.' )



if __name__ == '__main__':

    args = parser.parse_args()

    scf = SafeConfigParser()
    scf.read('pesman.config')


    # Change these to your liking
    dB = scf.get('DataBase', 'db')
    pesDir = scf.get('Directories', 'pesdir')
    exportDir = scf.get('Directories', 'expdir')
    molInfo = dict(scf.items('molInfo'))
    try:
        molInfo['extra'] = molInfo['extra'].split(',')
    except KeyError:
        molInfo['extra'] = []


    if args.subcommand == 'export':
        calcId = args.calc_id
        jobs = args.jobs
        depth = args.Depth
        gidList =args.gid_list
        sidList = args.sid_list
        templ = args.ComTemplate
        const = args.const
        inclp  = args.incl_path

        txt = textwrap.dedent("""
        ------------------------------------
                    PESMan Export
        ------------------------------------
        Database        : {}
        Calc Type Id    : {}
        PESDir          : {}
        Export Dir      : {}
        Number of Jobs  : {}
        Depth           : {}
        GeomID List     : {}
        SartID List     : {}
        Template        : {}
        Constraint      : {}
        Include Path    : {}
        """.format( dB, calcId, pesDir, exportDir, jobs, depth, gidList, sidList, templ if templ else 'Default', const, inclp))
        print(txt)
        ExportNearNbrJobs(dB, calcId, jobs,exportDir,pesDir, templ, gidList, sidList, depth, const, inclp, molInfo)


    # Execute an import command
    if args.subcommand == 'import':
        isZipped = args.zip
        iGl = args.ig
        isDel = args.delete
        txt = textwrap.dedent("""
        --------------------------------------
                    PESMan Import 
        --------------------------------------
        Database            : {}
        PES Dir             : {}
        Ignore files        : {}
        Delete after import : {}
        Archive directory   : {}
        """.format(dB, pesDir, iGl, isDel, isZipped))
        print(txt)
        for expFile in args.ExpFile: # accepts multiple export files
            ImportNearNbrJobs(dB, expFile, pesDir, iGl, isDel, isZipped)




    if args.subcommand=='zip':
        paths = args.d 
        allPat = args.all 
        for path in paths: # if d not provided, its empty anyway
            zipOne(path)
        
        # `-all` is an optional argument with optional values of unknown lenght
        # i.e `-all`, `-all abc` , `-all abc xyz` all are valid
        if allPat is not None:            # means `-all` flag is given
            if not allPat:                # `-all` is given without any values
                allPat = ['multi','mrci'] # some default if nothing is given
            zipAll(allPat)



    if args.subcommand=='unzip':
        for path in args.f:
            unZipOne(path)
        if args.all:
            unzipAll(args.all)
