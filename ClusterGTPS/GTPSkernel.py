'''
Created on July 27, 2010

@author: Wolfgang Lechner 
'''
import pygromacstps.tps as gtps
import sys

if __name__ == '__main__':
    basedir = ""
    dirnumber = 0
    mode = "tps"
    kernel = 0
    for arg in sys.argv[1:]:
        argument = arg.split("=")
        if argument[0] == "basedir":
            basedir = argument[1]
        elif argument[0] == "mode":
            mode = argument[1]
        elif argument[0] == "dirnumber":
            dirnumber = int(float(argument[1]))
        elif argument[0] == "kernel":
            kernel = int(float(argument[1]))
        else:
            print "argument should be one of those: basedir,mode, startwith,rstartwith,runs"
    if basedir!="":
        if mode == 'initial':
            sim = gtps.gromacstps(basedir,"initial",kernel)
            successfull = [False for x in sim.kernels.kernelPaths]
            k = 0
            while(True):
                sim.preperationFromStart()
                sim.shootingInitialGroFiles()
                sim.shootingQueue()
                sim.checkAllTpsPathsAccepted()
                sim.finalizeInitial()
                sim.outputAllFullTrajectories("0000000")
                for i in range(len(sim.kernels.kernelPaths)):
                    if sim.paths[i].tpsaccepted:
                        successfull[i] = True
                print k, successfull
                if any(successfull):
                    break
                k+=1
                sim.deleteScratchFiles()
#        
        elif mode == 'tps':
            dirstring = "%07d" % (dirnumber,)
            newdirstring = "%07d" % (dirnumber + 1,)
            sim = gtps.gromacstps(basedir,"tps",kernel)
            sim.preperationTPS()
            
            for i in sim.kernels.kernelPaths:
                sim.getFullTrajectory(i,dirstring)
                sim.paths[i].lastAcceptedFullTrajectory = sim.paths[i].fullTrajectory[:]
                sim.paths[i].lastAcceptedFullTrajectoryblength = sim.paths[i].fullTrajectoryblength
                sim.paths[i].lastAcceptedFullTrajectoryflength = sim.paths[i].fullTrajectoryflength
            
            sim.outputAllFullTrajectories(dirstring)
            sim.readLastAcceptedTrajectories(dirstring)
            sim.lastAcceptedToGro(dirstring)
            sim.pickConfigurationsTPS(dirstring)
            sim.shootingQueue()
            sim.checkAllTpsPathsAccepted()
            sim.finalizeTPS(dirstring,newdirstring)
            sim.outputAllFullTrajectories(newdirstring)
            sim.deleteOldTrrFiles(dirstring)
            sim.deleteScratchFiles()
            sim.writeFinishedFiles(newdirstring)
            print sim.kernels.kernelPaths
        elif mode== 'test':            
            dirstring = "%07d" % (dirnumber,)
            newdirstring = "%07d" % (dirnumber + 1,)
            sim = gtps.gromacstps(basedir,"tps",kernel)
            sim.preperationTPS()
            for i in sim.kernels.kernelPaths:
                sim.getFullTrajectory(i,dirstring)
                sim.paths[i].lastAcceptedFullTrajectory = sim.paths[i].fullTrajectory[:]
                sim.paths[i].lastAcceptedFullTrajectoryblength = sim.paths[i].fullTrajectoryblength
                sim.paths[i].lastAcceptedFullTrajectoryflength = sim.paths[i].fullTrajectoryflength
            
            sim.outputAllFullTrajectories(dirstring)
            sim.readLastAcceptedTrajectories(dirstring)
            sim.lastAcceptedToGro(dirstring)
            sim.pickConfigurationsTPS(dirstring)
            sim.shootingQueue()
            sim.checkAllTpsPathsAccepted()
            sim.finalizeTPS(dirstring,newdirstring)
            sim.outputAllFullTrajectories(newdirstring)
            sim.deleteOldTrrFiles(dirstring)
            sim.deleteScratchFiles()
            sim.writeFinishedFiles(newdirstring)
            print sim.kernels.kernelPaths