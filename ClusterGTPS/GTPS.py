'''
Created on May 3, 2010

@author: Wolfgang Lechner 
'''
import pygromacstps.tps as gtps
import sys
import os
import time


def shootingKernel(dirnumber):
    for i in range(sim.kernels.nkernels):
        pythonpath= sim.paths[0].options.paths["pythonpath"]
        mqsubs = sim.paths[0].options.runoptions["qsubsystem"]
        mwalltime = sim.paths[0].options.runoptions["qsubwalltime"]
        
        filename = sim.qsubsystem.writeKernelQsubFile(basedir, i,pythonpath,"tps",str(dirnumber),reverse=False,method="tps",qsubs=mqsubs,walltime=mwalltime)
        os.system("qsub " + filename)


def allFinished(dirstring):
    allF = True
    for i in sim.kernels.kernelPaths:
        lapath = sim.paths[i].nfsladir
        newladir = os.path.join(lapath,dirstring)
        filename = os.path.join(newladir,"finished")
        if not(os.path.exists(filename)):
            allF = False
    return allF


if __name__ == '__main__':

    basedir = os.getcwd()
    dirnumber = 0
    rdirnumber = 0
    runs = 1
    mode = "tps"
    for arg in sys.argv[1:]:
        argument = arg.split("=")
        if argument[0] == "basedir":
            basedir = argument[1]
        elif argument[0] == "mode":
            mode = argument[1]
        elif argument[0] == "startwith":
            dirnumber = int(float(argument[1]))
        elif argument[0] == "rstartwith":
            rdirnumber = int(float(argument[1]))
        elif argument[0] == "runs":
            runs = int(float(argument[1]))
        else:
            print "Arguments should be one of those: basedir, mode, startwith, rstartwith, runs"
            
    if basedir!="":
        if mode == 'initial': 
            sim = gtps.gromacstps(basedir,"initial",kernel="head")
            for i in range(sim.kernels.nkernels):
                pythonpath= sim.paths[0].options.paths["pythonpath"]
                mwalltime=sim.paths[0].options.paths["qsubwalltime"]
                
                filename = sim.qsubsystem.writeKernelQsubFile(basedir, i,pythonpath,"initial",0,method="tps",walltime=mwalltime)
                os.system("qsub " + filename)
                
        if mode == 'tps':
            
            dirstring = "%07d" % (dirnumber,)
            newdirstring = "%07d" % (dirnumber+1,)
            
            rdirstring = "%07d" % (rdirnumber,)
            rnewdirstring = "%07d" % (rdirnumber+1,)
            
            os.chdir(basedir)
            sim = gtps.gromacstps(basedir,"tps",kernel="head")
            
            for i in sim.kernels.kernelPaths:
                sim.getFullTrajectory(i, dirstring)
                sim.paths[i].lastAcceptedFullTrajectory = sim.paths[i].fullTrajectory[:]
            sim.outputAllFullTrajectories(dirstring)
            shootingKernel(dirnumber)
            
            
            while True:
                time.sleep(60)
                if allFinished(newdirstring):
                    break
                
            dirnumber += 1
            
            for run in range(runs):
                os.chdir(basedir)
                dirstring = "%07d" % (dirnumber,)
                newdirstring = "%07d" % (dirnumber+1,)
                shootingKernel(dirnumber)
                while True:
                    time.sleep(60)
                    if allFinished(newdirstring):
                        break
                dirnumber += 1
        if mode=="test":
            print "test\n"
            