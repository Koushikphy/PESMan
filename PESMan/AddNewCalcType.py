import sqlite3
from ConfigParser import SafeConfigParser
from itertools import izip_longest as izl

scf = SafeConfigParser()
scf.read('pesman.config')
db = scf.get('DataBase','db')
names = map(str.strip, scf.get('CalcTypes','type').split(','))
templates = map(str.strip, scf.get('CalcTypes','template').split(','))
try:
    desc = map(str.strip, scf.get('CalcTypes','desc').split(','))
except: # desc field not found
    desc = ''


with sqlite3.connect(db) as con: 
    cur = con.cursor()
    for nam, tem, des in izl(names, templates, desc):
        if not des: des = ''
        stemp = open(tem).read()
        cur.execute("INSERT INTO CalcInfo (Type,InpTempl,Desc) VALUES (?, ?, ?)", (nam, stemp,des))
    for row in cur.execute("SELECT * FROM CalcInfo"):  print row
    print "{} template inserted into database".format(len(templates))
