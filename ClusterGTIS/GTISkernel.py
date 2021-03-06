'''
Created on July 27, 2010

@author: Wolfgang Lechner 
'''
import pygromacstps.tis as gtis
import sys

if __name__ == '__main__':
    basedir = ""
    dirnumber = 0
    mode = "tis"
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
            sim = gtis.gromacstis(basedir,"initial",kernel)
            
            successfull = [False for x in sim.kernels.kernelPaths]

            k = 0
            while(True):
                sim.preperationFromStart()
                sim.preperationReverse()
                sim.shootingInitialGroFiles()
                
                if sim.kernels.dynamicshooting == 1:
                    sim.shootingQueueDynamic()
                else:
                    sim.shootingQueue()
                
                sim.checkAllTisPathsAccepted()
                sim.finalizeInitial()
                successfull = []
                for i in sim.kernels.kernelPaths:
                    successfull.append(sim.paths[i].tisaccepted)
                if all(successfull):
                    break
                k+=1
                sim.outputAllFullTrajectories("%07d" % (0,))
                sim.deleteScratchFiles()
        
            
        elif mode == 'tis':
            dirstring = "%07d" % (dirnumber,)
            newdirstring = "%07d" % (dirnumber + 1,)
            
            sim = gtis.gromacstis(basedir,"tis",kernel)
            print sim.kernels.kernelPathsAll
            sim.preperationTIS()
            sim.preperationReverse()
            sim.readLastAcceptedTrajectories(dirstring)
            sim.lastAcceptedToGro(dirstring)
            sim.pickConfigurationsTIS(dirstring)
            if sim.kernels.dynamicshooting == 1:
                sim.shootingQueueDynamic()
            else:
                sim.shootingQueue()
            
            sim.checkAllTisPathsAccepted()
            sim.finalizeTIS(dirstring,newdirstring)
            sim.outputAllFullTrajectories(newdirstring)
            sim.deleteOldTrrFiles(dirstring)
            sim.deleteScratchFiles()
            sim.writeFinishedFiles(newdirstring)
        elif mode=="test":
            sim = gtis.gromacstis(basedir,"tis",kernel)
            print sim.kernels.kernelPathsAll
            
    