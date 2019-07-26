#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@authors: Sham/Bijit/Saikat/Satrajit
"""

import argparse
import textwrap
import os
import sys
import ConfigParser

import ImpExp_new
import misc

# create the top-level parser
parser = argparse.ArgumentParser(
           prog='PESMan',
           #usage='Use "python %(prog)s --help" for more information',
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

# arguments for the main program
parser.add_argument('--version', action='version', version='%(prog)s 0.1')
parser.add_argument('-v', '--verbose', action='store_true', dest='Verbose', help='Increase output verbosity')
parser.add_argument('--db', action='store', dest='DbMain', metavar='DB',
         help=textwrap.dedent('''\
             Main data base file.
             This contains geometry grid, calculation types,
             completed and currently exported calculations.
             Default will be picked up from config file.\n
             '''))
parser.add_argument('--db-nbr', action='store', metavar='DB', dest='DbNbr',
         help=textwrap.dedent('''\
             Neighbour data base file.
             This contains info on neighbours of geometries.
             Used within certain export algorithms.
             Default will be picked up from config file.\n
             '''))
parser.add_argument('--pes-dir', action='store', metavar='DIR', dest='PESDir',
         help=textwrap.dedent('''\
             Directory containing PES data.
             This contains data of all completed calculations
             organized in a hierarchical directory structure.
             Default will be picked up from config file.\n
             '''))
parser.add_argument('--config', action='store', metavar='FILE', dest='ConfigFile', default='pesman.config',
         help=textwrap.dedent('''\
             Use alternate configuration file.
             Default is 'pesman.config' file which must be
             present in the same dir as this program.\n
             '''))

subparsers = parser.add_subparsers(title='Currently implemented sub-commands',dest='subcommand')

# create the parser for the "export" subcommand
#
# export subcommand:
#
# --dir         directory to place exported jobs.
#               if not given, read from pesman.config file.
# --jobs        number of jobs to export
# --calc-id     calculation type to export
# --geom-id     geometry to export
#               required only for single geometry exports
# --type        type of export (general, jacobi cut, linear cut, single geometry etc.,)
#               default is general
# --depth       depth parameter for exports involving near neighbour algorithms
# --template    use this template file instead of the default one.
# --incl-path   include pathological geometries in export
#               default is not to do this.
# --check       do not register the export
#               directory will be produced, but db is not modified.

parser_export = subparsers.add_parser('export',
                       formatter_class=argparse.RawTextHelpFormatter,
                       description=textwrap.dedent('''\
                       Export calculations of a certain type from the database.

                       A 'gen' type of export uses nearest neigbour algorithm to
                       search for best jobs to be exported, if there is dependency.
                       The data base is modified to reflect the export.
                       The .exp file generated can be used for subsequent import.'''),
                       help='Export calculations of a given type')

parser_export.add_argument('-d', '--dir', action='store', metavar='DIR', dest='ExportDir',
                           help='Directory to place exported jobs.')
parser_export.add_argument('-j', '--jobs', metavar='N', action='store', dest='NumJobs',
                           type=int, default=50, help='Number of exported jobs')
parser_export.add_argument('--calc-id', metavar='CID', action='store', dest='CalcTypeId',
                           type=int, required=True, help='Id of calculation type')
parser_export.add_argument('--geom-id', metavar='GID', action='store', dest='GeomId',
                           type=int, help='Id of geometry')
parser_export.add_argument('--gid-list', metavar='LGID', action='store', dest='GeomIdList', nargs='+',
                           type=int, default=[], help='List of one or more Gometry Ids')
parser_export.add_argument('--sid-list', metavar='LSID', action='store', dest='StartIdList', nargs='+',
                           type=int, default=[], help='List of one or more StartGeom Ids')
parser_export.add_argument('--type', metavar='TYPE', action='store', dest='ExpType',
                           choices=["gen","jac","single"], default="gen",
                           help='Type of export (default: general export)')
parser_export.add_argument('--depth', metavar='N', action='store', dest='Depth',
                           type=int, default=1,
                           help=textwrap.dedent('''\
                           Specify a depth parameter for near neighbour algorithms.
                           This will decide the search depth for finding exportable jobs.
                           The default is 1, which means nearest neighbour search.
                           Using zero or negative values or values beyond 3 requires
                           specification of a data base containing information on  neighbours.
                           Zero or negative values will invoke search based on distance.\n
                           '''))
parser_export.add_argument('--template', metavar='TEMPL', action='store', dest='ComTemplate',
                           default='', help='Template file for generating input files.')
parser_export.add_argument('--incl-path', action='store_true', dest='IncludePath',
                           help='Include pathological geometries')
parser_export.add_argument('--constraint', metavar='CONST', action='store', dest='ConstDb',
                           type=str, 
                           help=textwrap.dedent('''\
                           Specify a database constraint in the geometries to be exported. The format
                           must be SQLite3 query with correct keywords. The query to be done is only for
                           the Geometry table of the database and for depth in (1,2,3). Wrong field or 
                           keywords will return a SQLite3 error.\n
                           '''))
parser_export.add_argument('--check', action='store_false', dest='RegisterExport',
                           help=textwrap.dedent('''\
                           Do not register the export.
                           Can be used to inspect jobs that will be generated.
                           The export will not be registered into database.
                           The .exp file will not be generated.\n
                           '''))

# create the parser for the "import" subcommand
#
# import subcommand
#
# --exp         use .exp file generated during export to perform import
#  -e           this file contains all deails required for import
#               this is the only way previously exported calcs can be imported.
#               this is how it is normally operated.
#
# --file        use .calc file to perform import.
#  -f           do not allow if the calc has been exported
#               this allows for importing special calcs performed manually.
#               
# --dir         specify a directory for import.
#  -d           all .calc files within the directory are tried.
#
# NOTE: the above options must be mutually exclusive. Only one is allowed at a time.
#
# --id          Specify export id
#
# --check       perform dry run to check if import will work.
#               it is a good practice to do this before every import.
#               summarize the changes that will happen upon import.
 
parser_import = subparsers.add_parser('import',
                    description='Import calculations into the PES database.',
                    formatter_class=argparse.RawTextHelpFormatter,
                    help='Import a bunch of completed calculations')
group_imp = parser_import.add_mutually_exclusive_group(required=True)
group_imp.add_argument('-e','--exp', action='store', metavar='EF', dest='ExpFile',
                       help=textwrap.dedent('''\
                       Specify a .exp file for import.
                       This file would have been generated during export.'''))
group_imp.add_argument('-f', '--file', action='store', metavar='CF', dest='CalcFile',
                       help=textwrap.dedent('''\
                       Specify a .calc file for import.
                       This file will be scanned to perform import.
                       Import is not allowed if the job is already exported'''))
group_imp.add_argument('-d', '--dir', action='store', metavar='DIR', dest='CalcDir',
                       help=textwrap.dedent('''\
                       Specify a directory for import.
                       All .calc files in the directory will be tried.'''))
parser_import.add_argument('--id', metavar='EID', action='store', dest='ExportId',
                           type=int, default=0, help='ExportId of import.')
parser_import.add_argument('--check', action='store_true', dest='ImportCheck',
                           help=textwrap.dedent('''\
                           Perform a dry run to check if import will work.
                           Summary of changes that will happen is listed.
                           It is a good practice to do this before every import.'''))

# create the parser for the "query" subcommand
#
# The 'query' subcommand will handle tasks requiring queries to data base,
# any request to modify the database other than import/export.
# later on, more complex tasks such as building PES or generating plots
# can be added.
#
# --close     Close an export and expunge its remaining jobs from ExpCalc table.

parser_query = subparsers.add_parser('query',
                    description='Query or modify the PES database.',
                    formatter_class=argparse.RawTextHelpFormatter,
                    help='Query or modify the PES database.')
parser_query.add_argument('--close', metavar='EID', action='store', dest='ExportIdToClose', type=int, default=0,
                          help='Close an export and expunge remaining jobs from ExpCalc table.')

if __name__ == '__main__':

    # by default 'pesman.config' file is located in the same directory as this python file
    DefaultConfigDir = os.path.abspath(os.path.dirname(sys.argv[0]))

    # parse the command line arguments
    Args = parser.parse_args()

    # first check if a different config file is provided '--config'
    if not Args.ConfigFile:
       Args.ConfigFile = DefaultConfigDir + "/" + "pesman.config"

    # parse the config file through ConfigParser class
    ConfParser = ConfigParser.SafeConfigParser()
    ConfParser.read(Args.ConfigFile)

    # if any option has been passed through command line
    if not Args.DbMain:
       Args.DbMain = ConfParser.get('DB','main') # option 'main' can be case-insensitive
    if not Args.DbNbr:
       DbNbrConfig = ConfParser.get('DB','nbr')
    if not Args.PESDir:
       Args.PESDir = ConfParser.get('PESDATA','pesdir')
    
    # set defaults for export
    if Args.subcommand == 'export':

       if not Args.ExportDir:
          if ConfParser.has_option('EXPORT','ExpDir'):
             Args.ExportDir = ConfParser.get('EXPORT','ExpDir')

       # assert if values are meaningful
       if Args.NumJobs <= 0:
          raise Exception("Invalid argument for --jobs: " + str(Args.NumJobs))
       if Args.CalcTypeId <= 0:
          raise Exception("Invalid argument for --calc-id: " + str(Args.CalcTypeId))
       if Args.GeomId and Args.GeomId < 0:
          raise Exception("Invalid argument for --geom-id: " + str(Args.GeomId))
       if Args.GeomIdList:
          for i in Args.GeomIdList:
              if i <= 0:
                  raise Exception("Invalid argument in --gid-list: " + str(Args.GeomIdList))
       if Args.StartIdList:
          for i in Args.StartIdList:
              if i < 0:
                  raise Exception("Invalid argument in --sid-list: " + str(Args.StartIdList))
       if Args.ExpType != "gen":
          raise Exception("Unsupported option for --type: " + Args.ExpType)
       if Args.Depth > 3 or Args.Depth <= 0:
          if not Args.DbNbr:
             Args.DbNbr = DbNbrConfig
             if not Args.DbNbr:
                raise Exception("Chosen depth requires DbNbr: " + str(Args.Depth))
       if Args.ConstDb == '0':
          raise Exception("Cannot take Constraint input as '0'")

    # set defaults for import
    if Args.subcommand == 'import':

       # for the moment nothing much
       if Args.ExportId < 0:
          raise Exception("Invalid argument for --id: " + str(Args.ExportId))


    # Now execute subcommand invoked.

    # Execute an export command
    if Args.subcommand == 'export':

       print "PESMan: Export"
       print "**************"
       print "   Db         \t = ", Args.DbMain
       print "   DbNbr      \t = ", DbNbrConfig
       print "   CalcTypeId \t = ", Args.CalcTypeId
       print "   PESDir     \t = ", Args.PESDir
       print "   ExportDir  \t = ", Args.ExportDir
       print "   MaxJobs    \t = ", Args.NumJobs
       print "   Depth      \t = ", Args.Depth
       print "   GeomId     \t = ", Args.GeomId
       if Args.GeomIdList:
          print "   GeomIdList \t = ", "List of " + str(len(Args.GeomIdList)) + " geom(s)"
       if Args.StartIdList:
          print "   StartIdList\t = ", "List of " + str(len(Args.StartIdList)) + " startgeom(s)"
       print "   InclPath   \t = ", Args.IncludePath
       print "   Constraint \t = ", Args.ConstDb
       print "   Register   \t = ", Args.RegisterExport
       if Args.ComTemplate:
          print "   Template   \t = ", Args.ComTemplate
       else:
          print "   Template   \t =  Default Template"
       print

       if Args.ExpType == "gen":

          print "General Nearest Neighbour Export.\n"
          ImpExp.ExportNearNbrJobs(Args)

       print "\nPESMan: Successfully Exported!"

    # Execute an import command
    if Args.subcommand == 'import':

       print "PESMan: Import"
       print "**************"
       print "   Db         \t = ", Args.DbMain
       print "   DbNbr      \t = ", Args.DbNbr
       print "   PESDir     \t = ", Args.PESDir
       print

       # import based on 'export.dat' file
       if Args.ExpFile:

          Args.ExportDir = os.path.abspath(os.path.dirname(Args.ExpFile))
          print "Importing from export.dat file in directory",Args.ExportDir
          ImpExp.ImportNearNbrJobs(Args)

       # import from a '.calc' file
       if Args.CalcFile:

          CalcDir = os.path.abspath(os.path.dirname(Args.CalcFile))
          print "Importing from calc file ", Args.CalcFile
          ImpExp.ImportCalc(Args.DbMain,CalcDir,Args.CalcFile,Args.PESDir,
                            Verbose=Args.Verbose,Check=Args.ImportCheck)

       # import from all '.calc' files in directory
       if Args.CalcDir:

          print "Importing from all .calc files in directory ", Args.CalcDir
          misc.CheckDirAccess(Args.CalcDir,bRead=True,bAssert=True)
          CalcFilesDir = [ f for f in os.listdir(Args.CalcDir) if f.endswith(".calc") ]
          if len(CalcFilesDir) > 0:
             print len(CalcFilesDir), "calc files will be tried for import."
          else:
             print "No .calc files present in this directory."
          for CalcFile in CalcFilesDir:
              ImpExp.ImportCalc(Args.DbMain,Args.CalcDir,Args.CalcDir+"/"+CalcFile,Args.PESDir,
                                Verbose=Args.Verbose,Check=Args.ImportCheck)

       print "\nPESMan: Successfully Imported!"


    # Execute a query command
    if Args.subcommand == 'query':
       
       print "PESMan: Query "
       print "**************"
       print "   Db         \t = ", Args.DbMain
       print "   DbNbr      \t = ", Args.DbNbr
       print "   PESDir     \t = ", Args.PESDir

       if Args.ExportIdToClose != 0:

          ImpExp.CloseExport(Db=Args.DbMain,ExportId=Args.ExportIdToClose,Verbose=True)

          


       

         

       

          

