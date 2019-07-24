import re

txt = """
results for 1-2: Analytic Nacts ---  multinact2-geom111-111
       GRADX         GRADY     GRADZ
    -0.13424460    0.08801304    0.0
     0.03735361    0.02953837    0.0
     0.05766094   -0.11556212    0.0
                                                  

results for 1-2: Analytic Nacts ---  multinact2-geom111-111
       GRADX         GRADY     GRADZ
     0.77121078   -0.14513804    0.0
    -0.44182473   -0.08351556    0.0
    -0.32618068    0.22852658    0.0
                                                  
 """
print re.findall(r"(?:(?<=^)|(?<=\s))([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)(?=\s|$|\n|\r\n)", txt)
