def dummyRun(scrDir, proc, extra):
        """ Used only for debugging purpose"""
    
        with open("export.dat",'r') as f:
            sExpDat = f.read().split("\\n",1)[1]
        DirsToDo = [d for d in sExpDat.split() if os.path.isfile(d+"/"+d+".calc_")]
        for RunDir in DirsToDo:
            fComBaseFile = RunDir + ".com"
            with cd(RunDir):
                with open("%s.wfu"%RunDir, "w") as f: f.write("Nothing to see here")
                with open("%s.res"%RunDir, "w") as f: f.write("21 111 73")
                os.rename( "%s.calc_"%RunDir, "%s.calc"%RunDir)
    
    
    