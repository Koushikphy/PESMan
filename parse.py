import re 

with open('./multi1-geom1566-1.out') as f :
    txt = f.read()


pattern = '\s*(\d+).*\n\n\s*\*\* WVFN \*\*\*\*'

print re.findall(pattern, txt)