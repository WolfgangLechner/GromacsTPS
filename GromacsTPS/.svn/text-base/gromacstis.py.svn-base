'''
Created on May 3, 2010

@author: Wolfgang Lechner 
'''
import pygromacstps.tis as gtis
import sys

if __name__ == '__main__':
    
    if len(sys.argv) == 1:
        print 'excepted parameters are "initial" and "tis"'
    else:
        if sys.argv[1] == 'initial': 
            sim = gtis.gromacstis("/home/cpd/wolf/membranes/firsttis","initial")
            sim.preperationFromStart()
            sim.reverseBackwardGroFile()
            for i in range(10):
                sim.shootingGroFile()
                sim.shootingQueue()
                sim.finalizeShooting("%07d" % i)
        elif sys.argv[1] == 'tis':
            sim = gtis.gromacstis("/home/cpd/wolf/membranes/firsttis","tis")
            
            sim.getStartTrajectories()
            #sim.trialReplicaExchange("0000000")
            sim.preperationTIS()
            sim.lastAcceptedToGro("start")
            sim.pickConfigurationsTIS("start")
            sim.shootingQueue()
            sim.checkAllTisPathsAccepted()
            sim.updateCrossingHistos()
            
            dirnumber = "%07d" % 0
            sim.finalizeTIS(dirnumber)
            sim.outputAllFullTrajectories(dirnumber)
            for i in range(1,10):
                dirnumber = "%07d" % (i,)
                olddirnumber = "%07d" % (i - 1,)
                sim.lastAcceptedToGro(olddirnumber)
                sim.pickConfigurationsTIS(olddirnumber)
                sim.shootingQueue()
                sim.checkAllTisPathsAccepted()
                sim.finalizeTIS(dirnumber)
                sim.outputAllFullTrajectories(dirnumber)
                sim.updateCrossingHistos()
                sim.outputAllCrossingHistos()
                sim.deleteOldTrrFiles(olddirnumber)
        elif sys.argv[1] == 'test':
            sim = gtis.gromacstis("/Users/wolf/work/projects/membranes/data/run/dopcvalTIS","tis")
            sim.getStartTrajectories()
            sim.trialReplicaExchange("0000000")
    
    
    
    
    
    
    
    
    
    
    