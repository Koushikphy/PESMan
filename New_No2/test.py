import sqlite3 
import os
sql_script = """
BEGIN TRANSACTION;
CREATE TABLE Geometry(
Id INTEGER PRIMARY KEY,
rho REAL,
phi REAL,
Tags TEXT,
Nbr TEXT);
CREATE TABLE CalcInfo(
Id INTEGER PRIMARY KEY,
Type TEXT NOT NULL,
InpTempl TEXT NOT NULL,
Desc TEXT);
CREATE TABLE Calc(
Id INTEGER PRIMARY KEY,
GeomId INTEGER NOT NULL,
CalcId INTEGER NOT NULL,
Dir TEXT NOT NULL,
StartGId INTEGER NOT NULL,
Results TEXT);
CREATE TABLE ExpCalc(
ExpId INTEGER NOT NULL,
GeomId INTEGER NOT NULL,
CalcDir TEXT NOT NULL);
CREATE TABLE Exports(
Id INTEGER PRIMARY KEY,
Type INTEGER DEFAULT 0,
CalcType INTEGER NOT NULL,
NumCalc INTEGER DEFAULT 0,
Status INTEGER DEFAULT 0,
ExpDT DATETIME,
ExpDir TEXT,
ImpDT TEXT,
ImpGeomIds TEXT);
END TRANSACTION;
"""
os.remove('test.db')
newGeomList = [[1,2],[2,3],[4,5]]



con = sqlite3.connect('test.db')
try:
    with con:
        con.executescript(sql_script)
        con.executemany('INSERT INTO Geometry (rho,phi) VALUES (?, ? )', newGeomList)
        con.commit()
except:
    pass