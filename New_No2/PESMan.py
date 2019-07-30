#!/usr/bin/env python

import argparse
import textwrap
import ConfigParser
from ImpExp import ImportNearNbrJobs, ExportNearNbrJobs


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

parser.add_argument('--config', action='store', metavar='FILE', dest='ConfigFile', default='pesman.config',
            help=textwrap.dedent('''\
             Use alternate configuration file.
             Default is 'pesman.config' file which must be
             present in the same dir as this program.\n
             '''))

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
parser_export.add_argument('--constraint', metavar='CONST', dest='ConstDb', type=str,  help='Specify a database constraint in SQLite3 query format for the geometries to be exported.\n ' )

 
parser_import = subparsers.add_parser('import', description='Import calculations into the PES database.',
                    formatter_class=argparse.RawTextHelpFormatter,
                    help='Import a bunch of completed calculations')

parser_import.add_argument('-e','--exp', metavar='EF', dest='ExpFile',required=True, help=''' Specify a .exp file for import, generated during export.\n ''')
# parser_import.add_argument('-id', metavar='EID', dest='ExportId', type=int, default=0, help='ExportId for import.\n ')
parser_import.add_argument('-ig', metavar="LIST", nargs='+',  type=str, default=[],help="List file extensions to ignore during import\n ")
parser_import.add_argument('-del', default=False,dest='delete', action="store_true" ,help="Delete folder after successful import")
parser_import.add_argument('-nz','--no-zip',default = True, action = "store_false", help = textwrap.dedent('''
                            During import, by default the data folders are compressed into an archive by bzip2. 
                            Although this reduces total size and file number substantially, this is a CPU heavy process 
                            and compressing and decompressing takes considerable time. Use this argument to import without compressing.
                            '''))



if __name__ == '__main__':

    args = parser.parse_args()
    ConfParser = ConfigParser.SafeConfigParser()
    ConfParser.read(args.ConfigFile)


    dB = ConfParser.get('DB','main')
    pesDir = ConfParser.get('PESDATA','pesdir')
    
    if args.subcommand == 'export':
        exportDir = ConfParser.get('EXPORT', 'ExpDir')
        calcId = args.calc_id
        jobs = args.jobs
        depth = args.Depth
        gidList =args.gid_list
        sidList = args.sid_list
        templ = args.ComTemplate
        const = args.ConstDb
        incl  = args.incl_path

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
        """.format( dB, calcId, pesDir, exportDir, jobs, depth, gidList, sidList, templ if templ else 'Default', const, incl))
        print(txt)
        ExportNearNbrJobs(dB, calcId, jobs,exportDir,pesDir, templ, gidList, sidList, depth, const, incl)


    # Execute an import command
    if args.subcommand == 'import':
        isZipped = args.no_zip
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
        ImportNearNbrJobs(dB, args.ExpFile, pesDir, iGl, isDel, isZipped)
