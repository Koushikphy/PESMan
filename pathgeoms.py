#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3

with sqlite3.connect("h3db.db") as con:
   con.row_factory=sqlite3.Row
   cur = con.cursor() 
   cur.execute("SELECT Id FROM Geometry WHERE tags not LIKE '%path%'")
   lrow = cur.fetchall()
   PathGeomIds = []
   for row in lrow:
       PathGeomIds.append(row["Id"])
print len(PathGeomIds)

