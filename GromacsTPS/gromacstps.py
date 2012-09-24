'''
Created on May 3, 2010

@author: Wolfgang Lechner 
'''
import pygromacstps.tps as gtps
import sys

if __name__ == '__main__':
    
    if len(sys.argv) == 1:
        print 'excepted parameters are "initial" and "tps"'
    else:
        if sys.argv[1] == 'initial': 
            sim = gtps.gromacstps("/Users/wolf/work/projects/membranes/data/run/dopcvalTPS","initial")
            sim.preperationFromStart()
            sim.reverseBackwardGroFile()
            for i in range(10):
                sim.shootingGroFile()
                sim.shootingQueue()
                sim.finalizeShooting("%07d" % i)
        elif sys.argv[1] == 'tps':
            sim = gtps.gromacstps("/Users/wolf/work/projects/membranes/data/run/dopcvalTPS","tps")
            
            sim.preperationTPS()
            sim.lastAcceptedToGro("start")
            sim.pickConfigurationLastAccepted("start")
            sim.shootingQueue()
            dirnumber = "%07d" % 0
            sim.finalizeShooting(dirnumber)
            sim.finalizeCopyLastAccepted(dirnumber)
            for i in range(1,10):
                dirnumber = "%07d" % (i,)
                olddirnumber = "%07d" % (i - 1,)
                sim.lastAcceptedToGro(olddirnumber)
                sim.pickConfigurationLastAccepted(olddirnumber)
                sim.shootingQueue()
                sim.finalizeShooting(dirnumber)
                sim.finalizeCopyLastAccepted(dirnumber)
                traj = sim.getFullTrajectory(True,dirnumber)
                traj = sim.getFullTrajectory(False,dirnumber)
                
            
            
            
            
        