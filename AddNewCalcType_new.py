import sqlite3

def addNewCalcType(db, conf):
    with sqlite3.connect(db) as con: 
        cur = con.cursor()
        for tconf in conf:
            stemp = open(tconf['template']).read()
            cur.execute("""INSERT INTO CalcInfo (Type,InpTempl,OrbRec,Desc) VALUES (?, ?, ?, ?)""", tconf["type"], stemp,tconf["record"],tconf["desc"])
        for row in cur.execute("SELECT * FROM CalcInfo"):  print row
        print "Record inserted and closed"


db = "fh2db.db"

conf = [{
    "type": "multi",
    "template": "./multi-722-1-avtz.template",
    "record": "2901.2",
    "desc": ""},
    
    "type": "multinact",
    "template": "./ananact.template",
    "record": "2350.2",
    "desc": ""},
    ]
AddNewCalcType(db,conf)

