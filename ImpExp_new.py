import re 
import numpy as np 

def parseResult(file):
    # reads a file and returns the result as a string
    with open(file, 'r') as f:
        txt = f.read()
    txt = txt.replace('D','E')
    res = re.findall(r"(?:(?<=^)|(?<=\s))([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)(?=\s|$|\n|\r\n)", txt)
    return ' '.join(res)

