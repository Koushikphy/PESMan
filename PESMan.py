#!/usr/bin/env python

import os,sys
import shutil
import logging 
import tarfile
import argparse
import textwrap
from itertools import izip_longest as izl
from ConfigParser import SafeConfigParser
from ImpExp import ImportNearNbrJobs, ExportNearNbrJobs
# from logging.handlers import TimedRotatingFileHandler


class MyFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt="%I:%M:%S %p %d-%m-%Y"):
        logging.Formatter.__init__(self, fmt, datefmt)

    def format(self, record):
        if record.levelno == logging.INFO: self._fmt = "%(message)s"
        elif record.levelno == logging.DEBUG: self._fmt = "[%(asctime)s] - %(message)s"
        result = logging.Formatter.format(self, record)
        return result


def makeLogger(logFile, stdout=False):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = MyFormatter()
    fh = logging.FileHandler(logFile)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # fht = TimedRotatingFileHandler(logFile, when="midnight",backupCount=10)
    # logger.addHandler(fht)
    if stdout:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger



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



# delete geomdatas from a list of geomids
def deleteCalcs(dB, pesDir, calcId, geomIdList):
    import sqlite3
    geomStr = ' where calcid = %s and geomid in ('%calcId + ','.join(map(str, geomIdList)) + ')'

    with sqlite3.connect(dB) as con:
        cur = con.cursor()

        cur.execute('select geomid from expcalc' + geomStr)
        for (geomId,) in cur:
            cur.execute('delete from expcalc where geomid = ? and calcid = ?',(geomId,calcId))
            print("CalcId = {}, GeomId = {} deleted from ExpCalc Table".format(calcId,geomId))

        cur.execute('select type from CalcInfo where id=?',(calcId,))
        calcName = cur.fetchone()[0]
        cur.execute('select geomid from calc' + geomStr)
        for (geomId,) in cur:
            dirToRemove = '{}/geom{}/{}{}'.format(pesDir, geomId,calcName, calcId)
            if os.path.isdir(dirToRemove): # geomdata is in folder format
                shutil.rmtree(dirToRemove)
            elif os.path.isfile(dirToRemove+'.tar.bz2'): # if is it in archived
                os.remove(dirToRemove+'.tar.bz2')
            else:
                print("No GeomData found for CalcId = {}, GeomId = {}".format(calcId,geomId) )
            cur.execute('delete from calc where geomid = ? and calcid = ?',(geomId,calcId))
            print("CalcId = {}, GeomId = {} deleted from CalcTable and GeomData".format(calcId,geomId))


def status(dB):
    import sqlite3
    with sqlite3.connect(dB) as con:
        cur = con.cursor()
        status = '-'*75+'\033[31m\n\033[5m\033[4mPESMan Status:\033[0m\t\t'
        cur.execute('select count(id) from Geometry')
        status+= '\033[35m\033[4mTotal number of geometries: {}\033[0m\n'.format(cur.fetchone()[0])
        cur.execute('select type from CalcInfo')
        names = [i[0] for i in cur]
        if len(names)==0:
            status+='{0}{1}{0}'.format('='*75,'\n\t\tNo Calcs are avialable\n')
            print(status)
            return
        status += "{0}\n{1:^10}|{2:^13}|{3:^20}|{4:^20}\n{0}".format('='*75,'CalcId','CalcName','Exported Jobs No.','Imported Jobs No.')
        for i,name in enumerate(names, start=1):
            cur.execute('select sum(NumCalc) from Exports where calcid=?',(i,))
            tE = cur.fetchone()[0]
            cur.execute('select sum(NumCalc) from Exports where calcid=? and status=1',(i,))
            tD = cur.fetchone()[0]
            status +="\n{:^10}|{:^13}|{:^20}|{:^20}\n".format(i,name,tE,tD)
        print(status+'-'*75)




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

subparsers.add_parser('addcalc', description="Add Calculation info defined in 'pesman.config'", help= "Add Calculation info defined in 'pesman.config'")
subparsers.add_parser('status', description='Check current PESMan Status\n ', help= 'Check current PESMan Status')



parser_zip = subparsers.add_parser('zip', description='Archive one/multiple directory or all individual geom folders.\n ', help = 'Archive one/multiple directory or all individual geom folders.')
parser_zip.add_argument('-d', metavar="LIST", nargs='+', type=str, default=[], help='Provide path(s) of folder(s) to archive.\n ' )
parser_zip.add_argument('-all' ,metavar="DIR", nargs='*', type=str, help='Use this flag to archive all geom folders by default.\nAdditionally provide folder names to to search for to archive.' )

parser_unzip = subparsers.add_parser('unzip', description='Extract one/multiple directory or all individual archived geom folders.\n ', help= 'Extract one/multiple directory or all individual archived geom folders.')
parser_unzip.add_argument('-f', metavar="LIST", nargs='+', type=str, default=[], help='Provide path(s) of file(s) to unarchive.\n ')
parser_unzip.add_argument('-all' ,metavar="ROOT",nargs='?',const='.', type=str, help='Use this flag to unarchive all geom folders by default.\nAdditionally provide root folder where to search for.' )


parser_delete = subparsers.add_parser('delete', description='Delete one/multiple geometry data\n ', help= 'Delete one/multiple geometry data',formatter_class=argparse.RawTextHelpFormatter,)
parser_delete.add_argument('-gid', metavar="GID",nargs='+', type=str, required=True, help='Provide one or multiple geomids to remove.\nUse "-" to provide a range.\n ')
parser_delete.add_argument('-cid' ,metavar="CID", type=str,required=True, help='Provide the calcid to remove.\n ' )






if __name__ == '__main__':
    args = parser.parse_args()

    scf = SafeConfigParser()
    scf.read('pesman.config')

    dB = scf.get('DataBase', 'db')
    if not os.path.exists(dB) : raise Exception("DataBase %s doesn't exists"%dB)
    logFile = scf.get('Log', 'LogFile')
    logger = makeLogger(logFile=logFile, stdout=True)
    pesDir = scf.get('Directories', 'pesdir')


    if args.subcommand == 'export':    # expport jobs
        exportDir = scf.get('Directories', 'expdir')
        molInfo = dict(scf.items('molInfo'))
        try:
            molInfo['extra'] = molInfo['extra'].split(',')
        except KeyError:
            molInfo['extra'] = []

        calcId = args.calc_id
        jobs = args.jobs
        depth = args.Depth
        gidList =args.gid_list
        sidList = args.sid_list
        templ = args.ComTemplate
        const = args.const
        inclp  = args.incl_path

        txt = textwrap.dedent("""  PESMan Export
-------------------------------------------------
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
        logger.info('-------------------------------------------------')
        logger.debug(txt)
        try:
            ExportNearNbrJobs(dB, calcId, jobs,exportDir,pesDir, templ, gidList, sidList, depth, const, inclp, molInfo,logger)
        except AssertionError as e:
            logger.info('PESMan Export failed. %s'%e)
        except:
            logger.exception('PESMan Export failed')


    elif args.subcommand == 'import':  # import jobs
        isZipped = args.zip
        iGl = args.ig
        isDel = args.delete
        txt = textwrap.dedent("""PESMan Import 
-------------------------------------------------
        Database            : {}
        PES Dir             : {}
        Ignore files        : {}
        Delete after import : {}
        Archive directory   : {}
        """.format(dB, pesDir, iGl, isDel, isZipped))
        logger.info('-------------------------------------------------')
        logger.debug(txt)
        try:
            for expFile in args.ExpFile: # accepts multiple export files
                ImportNearNbrJobs(dB, expFile, pesDir, iGl, isDel, isZipped, logger)
        except AssertionError as e:
            logger.info('PESMan Import failed. %s'%e)
        except:
            logger.exception('PESMan import failed')



    elif args.subcommand == 'addcalc': # add calculation infos
        import sqlite3
        names = map(str.strip, scf.get('CalcTypes','type').split(','))
        templates = map(str.strip, scf.get('CalcTypes','template').split(','))
        try:
            desc = map(str.strip, scf.get('CalcTypes','desc').split(','))
        except: # description field not found
            desc = ''

        with sqlite3.connect(dB) as con: 
            cur = con.cursor()
            for nam, tem, des in izl(names, templates, desc, fillvalue=''):
                stemp = open(tem).read()
                cur.execute("INSERT INTO CalcInfo (Type,InpTempl,Desc) VALUES (?, ?, ?)", (nam, stemp,des))
                print "Template : '{}' inserted into database".format(nam)
            print "\n{0}\n{1:^10}{2:^15}{3:^20}{4:<20}\n{0}".format('='*99,'CalcType', "CalcName", "Description", 'Template')
            for row in cur.execute("SELECT Id,Type,desc,inptempl FROM CalcInfo"):
                row = [str(i).split('\n') for i in row]
                for line in izl(*row, fillvalue=''):
                    print '{:^10}{:^15}{:^20}{:<20}'.format(*line)
                print '-'*99


    elif args.subcommand=='zip': # archive directiories
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



    elif args.subcommand=='unzip': # unarchive directories
        for path in args.f:
            unZipOne(path)
        if args.all:
            unzipAll(args.all)



    elif args.subcommand== 'delete': # delete data
        calcId = args.cid
        gid = args.gid
        logger.debug('Deleting GeomIds: {}'.format(gid))
        geomIdList = []
        for ll in gid:
            c = [int(i) for i in ll.split('-')]
            if len(c)==2: # a range is given, flat it out
                c = [c[0]+i for i in range(c[1]-c[0]+1)]
            geomIdList.extend(c)
        deleteCalcs(dB, pesDir, calcId, geomIdList)



    elif args.subcommand =='status': # check pesman status
        status(dB)



##use this code to check if the neighbour path sequence breaks somewhere in database
# starting from `sid`
def checkBreaks(dB, sid):
    import sqlite3

    con = sqlite3.connect(dB)
    cur = con.cursor()

    cur.execute('select id,nbr from geometry')
    allGeom = [[i, map(int,j.split())] for i,j in cur]

    doneGeom = {sid}  # initial start id
    noNbr = []
    for geom,nbr in allGeom:
        if geom in doneGeom: continue
        for nn in nbr:
            if nn in doneGeom:
                doneGeom.add(geom)
                break
        else:
            print geom
            doneGeom.add(geom)