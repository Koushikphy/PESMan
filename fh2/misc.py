import math
import os
import os.path

def strip_float(s):
    """ return stripped version of string containing formatted numeric data
        remove leading and trailing spaces and apply special consideration for trailing zeros
        appearing after decimal point, if there is any """
    st = s.strip()
    ls = st.split(".",1)
    if len(ls) > 1:
       # decimal point present
       s1 = ls[0].lstrip('0')
       s2 = ls[1].rstrip('0')
       if not s1:
          s1 = "0"
       if not s2:
          s2 = "0"
       snew = s1 + "." + s2
    else:
       # could be integer
       snew = ls[0].lstrip('0')
    return snew

def ToAngs(f):
    """ au to angs """
    return f*0.529177209

def ToBohrs(f):
    """ angs to au """
    return f/0.529177209

def ToDeg(a):
    """ radians to degrees """
    return a*180.0/math.pi

def ToRad(a):
    """ degrees to radians """
    return a*math.pi/180.0

def dotp(x,y):
    """ dot product of two pairs """
    return x[0]*y[0] + x[1]*y[1]

def AreaTriangle(a,b,c):
    """ area of a tringle with sides a,b,c """
    ps = (a+b+c)/2.0
    ar = ps*(ps-a)*(ps-b)*(ps-c)
    # negative area due to round off errors set to zero
    if ar < 0.0:
        ar = 0.0
    ar = math.sqrt(ar)
    return ar

def CheckFileAccess(FileName,bRead,bAssert):
    """ Checks if File exists and has read/write access.
        if it exists and is read/write able  -- return True
	if it exists and not read/write able --
	   if bAssert is True  -- then it bombs out
	   if bAssert is False -- it return False
	if it does not exist --
	   if bAssert is True  -- then it bombs out
	   if bAssert is False -- it return False
	bRead is true to check Read access and false to check write access
    """
    # first check if it exists
    ret_ex = os.access(FileName,os.F_OK)
    if ret_ex:
       # file exists, check if it is file
       bFile = os.path.isfile(FileName)
       if bFile:
          # it is file, check if it is read/write able
          if bRead:
             ret_ac = os.access(FileName,os.R_OK)
          else:
             ret_ac = os.access(FileName,os.W_OK)
          if bAssert:
             if not ret_ac:
                raise Exception("Access bRead=" + str(bRead) + "for File=" + FileName)
          else:
             return ret_ac
       else:
          # it is not a file, then we should not be calling this
	  raise Exception("This routine should be called only for files")
    else:
       # file does not exist, decide based on bAssert
       if bAssert:
          raise Exception("File=" + FileName + " does not exist")
       else:
          return False

def CheckDirAccess(DirName,bRead,bAssert):
    """ Checks if Dir has read/write access.
        this is different from file permissions flags.
	A directory is said to read access if we can get into it and read a file (if file has permissions)
	  such a thing is possible if directory has "execute permission flag 'x' flag set
	A directory is said to have write access if we can get into it and write a new file in there.
	  such a thing requires if it has "write permission flag 'w' set

        if it exists and is read/write able  -- return True
	if it exists and not read/write able --
	   if bAssert is True  -- then it bombs out
	   if bAssert is False -- it return False
	if it does not exist --
	   if bAssert is True  -- then it bombs out
	   if bAssert is False -- it return False
	bRead is true to check Read access and false to check write access
    """
    # first check if it exists
    ret_ex = os.access(DirName,os.F_OK)
    if ret_ex:
       # dir exists, check if it is dir
       bDir = os.path.isdir(DirName)
       if bDir:
          # it is dir, check if it is read/write able
          if bRead:
	     # you are checking for read access to directory
	     # I call this read access becoz you can go in
             ret_ac = os.access(DirName,os.X_OK)
          else:
	     # you are checking for write access
	     # this requires you to go in and also have write permission there
             ret_ac = os.access(DirName,os.X_OK) and os.access(DirName,os.W_OK)
          if bAssert:
             if not ret_ac:
                raise Exception("Access bRead=" + str(bRead) + "for Dir=" + DirName)
          else:
             return ret_ac
       else:
          # it is not a dir, then we should not be calling this
	  raise Exception("This routine should be called only for directories")
    else:
       # file does not exist, decide based on bAssert
       if bAssert:
          raise Exception("Dir=" + DirName + " does not exist")
       else:
          return False





