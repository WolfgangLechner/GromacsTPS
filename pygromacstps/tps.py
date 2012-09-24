
'''
Created on May 3, 2010

@author: Wolfgang Lechner
'''


import wrappers
import parser
import pathdata
import filesystem
import gtpslogging
import helpers
import kernels
import qsubsystem
import random
import multiprocessing
import os
import subprocess
import time

class gromacstps(object):
    """
    Main TPS class which stores the paths, interfaces, stable states, and  paths. The class 
    also uses the gromacswrapper class, the filesystem class and helper.py. The logger is 
    self.log.
    """
    def __init__(self,basedir=".",mode="initial",kernel=0):
        self.basedir = basedir
        self.mode = mode
        self.cores = multiprocessing.cpu_count()
        self.wrapper = wrappers.gromacswrapper()
        self.distparser = parser.gdistparser()
        self.filesystem = filesystem.filesystem()
        self.helper = helpers.helpers()
        self.kernels = kernels.kernels(kernel)
        self.qsubsystem = qsubsystem.qsubsystem()
        
        #Initialize the logger
        if kernel=="head":
            self.log = gtpslogging.log("info",basedir,kernel)
        else:
            self.log = gtpslogging.log("debug",basedir,kernel)
        self.log.log.debug("logfile created")
        self.log.log.info(str(self.cores) + " CPUs detected")
        
        self.kernels.readKernelOptions(os.path.join(basedir,"options","kerneloptions.txt"))
        
        #read the stables states from a file
        self.stablestates.readStates(os.path.join(basedir,"options","stablestates.txt"))
        self.log.log.info("Read States : " + str(self.stablestates.states))
        
        """
        This array holds all the information about the paths. Each trajectory consists of a 
        forward-part and a backward-part. The trajectory can either be a forward trajectory
        or a backward trajectory. Forward trajectroies start in A.
        """
        
        self.paths = []
        self.npaths = 0
        for i in range(self.kernels.ntps):
            self.paths.append(pathdata.pathdata(i,basedir,mode,forward=True,forwardpart=True,interface=0))
            self.paths.append(pathdata.pathdata(i,basedir,mode,forward=True,forwardpart=False,interface=0))
            self.npaths += 1
        
        self.kernels.generateKernelLists(self.npaths)
        
        
    """ 
    ************************************************************************
    
        Initial Procedure
        
        Set of functions used for the generation of initial trajectories
    
    ************************************************************************
    """
    
    
    def preperationFromStart(self,copyfiles = True):
        """
        Creating the directory structure and copying standardfiles there, given that copyfile = True
        """
        for i in self.kernels.kernelPathsAll:
            initdir = self.paths[i].options.paths["initialpath"]
            workdir = self.paths[i].workdir
            dirlist = [self.paths[i].srcatchbase,self.paths[i].baseworkdir,self.paths[i].workdir,os.path.join(workdir,'paths')]
            self.filesystem.createDirList(dirlist, self.log.log)            
            
            dirlist = [os.path.join(initdir,'la'),self.paths[i].nfsbaseworkdir,self.paths[i].nfsladir]
            self.filesystem.createDirList(dirlist, self.log.log)             
            
            if copyfiles:  
                for file in self.paths[i].options.standardfiles:
                    self.filesystem.copyFiles(os.path.join(initdir,"standardfiles",file), workdir)
            
            
    
    def shootingInitialGroFiles(self):
        """
        Perform a shooting move on a gro file.
        """
        for i in self.kernels.kernelPaths:
            conffile = os.path.join(self.paths[i].workdir,"conf.gro")
            bakfile = os.path.join(self.paths[i].workdir,"bakconf.gro")
            bconffile = os.path.join(self.paths[i].workdir,"bconf.gro")
            self.helper.shootVelocities(conffile, bconffile)  
            self.filesystem.moveFile(conffile, bakfile)
            self.filesystem.moveFile(bconffile, conffile)
            dest = self.paths[i+1].workdir
            self.filesystem.copyFiles(conffile, dest)
            self.reverseBackwardGroFile(i+1)
            
            
            
                         
    def finalizeInitial(self):
        
        def _copyFiles(fromdir,destdir):
            self.filesystem.copyFiles(os.path.join(fromdir,"index.ndx"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"topol.tpr"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"traj.trr"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"traj.xtc"), destdir)
        
        dirnumber = "%07d" % 0
        for i in self.kernels.kernelPaths:
            if self.paths[i].tpsaccepted:
                baseladir = os.path.join(self.paths[i].options.paths["initialpath"],"la")
                lapath = self.paths[i].nfsladir
                newladir = os.path.join(lapath,dirnumber)
                newladirf = os.path.join(newladir,"forward")
                newladirb = os.path.join(newladir,"backward")
                dirlist = [baseladir,lapath,newladir,newladirf,newladirb]
                self.filesystem.createDirList(dirlist, self.log.log)
                
                _copyFiles(os.path.join(self.paths[i].workdir), newladirf)
                _copyFiles(os.path.join(self.paths[i+1].workdir), newladirb)
                
    
    def deleteScratchFiles(self):
        scratch = os.path.join(self.paths[0].options.paths["scratchpath"],"GTIS")
        os.system("rm -r " + scratch)
        
        
    """ 
    ************************************************************************
    
        TIS Procedure
        
        Set of functions that perform a TIS shooting
    
    ************************************************************************
    """

    def preperationTPS(self,copyfiles = True):
        """
        Creating the directory structure and copying standardfiles there, given that copyfile = True
        """
                       
        for i in self.kernels.kernelPathsAll:
            initdir = self.paths[i].options.paths["initialpath"]
            workdir = self.paths[i].workdir
            dirlist = [self.paths[i].srcatchbase,self.paths[i].baseworkdir,self.paths[i].workdir,os.path.join(workdir,'paths'),os.path.join(workdir,"latemp")]
            self.filesystem.createDirList(dirlist, self.log.log)            
            
            dirlist = [os.path.join(initdir,'all'),os.path.join(initdir,'la'),self.paths[i].nfsbaseworkdir,self.paths[i].nfsladir]
            self.filesystem.createDirList(dirlist, self.log.log)             
            
            if copyfiles:  
                for file in self.paths[i].options.standardfiles:
                    self.filesystem.copyFiles(os.path.join(initdir,"standardfiles",file), workdir)
            
    
    def getStartTrajectories(self):
        for i in self.kernels.kernelPaths:
            self.getFullTrajectory(i,dirstring = "start")
            self.paths[i].lastAcceptedFullTrajectory = self.paths[i].fullTrajectory[:]
            self.paths[i+1].lastAcceptedFullTrajectory = self.paths[i+1].fullTrajectory[:]
            self._outputFullTrajectory(os.path.join(self.paths[i].ladir,"start"), i,"start")
    
    """ 
    ************************************************************************
    
        Shooting procedure
    
    ************************************************************************
    """
    
    def lastAcceptedToGro(self,dirnumber):
        """
        The last accepted trajectory is transformed into gro files using trjconv. 
        """
        for i in self.kernels.kernelPathsAll:
            
            
            mpath = self.paths[i]
            fbdir = mpath.forwardpart and "forward" or "backward"
            nfsworkdir = os.path.join(mpath.nfsladir,dirnumber,fbdir)
            latemp = mpath.latemp
            self.filesystem.copyFiles(os.path.join(nfsworkdir,"traj.trr") , latemp)
            self.filesystem.copyFiles(os.path.join(nfsworkdir,"index.ndx") , latemp)
            self.filesystem.copyFiles(os.path.join(nfsworkdir,"topol.tpr") , latemp)
            cmd = self.wrapper.generateTrjconvCommand(mpath.options,latemp,latemp)
            self.wrapper.executeCommand(cmd, tinput="0")
            
    
    def pickConfigurationsTPS(self,dirnumber):
        for i in self.kernels.kernelPaths:
            self.pickConfigurationLastAccepted(dirnumber,i)  
    
    def pickConfigurationLastAccepted(self,dirnumber,pathnumber):
        """
        A random configuration is taken from a trajectory and the shooting move is performed.
        and copy the files to the workdir of the path.
        """
        fdir = os.path.join(self.paths[pathnumber].latemp)
        flist = self.filesystem.getFileList(fdir, "path*.gro")
        fsize = len(flist)
        bdir = os.path.join(self.paths[pathnumber+1].latemp)
        blist = self.filesystem.getFileList(bdir, "path*.gro")
        bsize = len(blist)
        
        sum = fsize + bsize
        
        rn = random.randint(0,sum-2)
        backwardpart = (rn < bsize)
        if backwardpart:
            file = os.path.join(bdir,"path%d.gro" % (rn))
        else:
            file = os.path.join(fdir,"path%d.gro" % (rn-bsize))
        
        self.log.log.debug(dirnumber + " " + str(pathnumber) +" " + str(rn) +  " " + str( sum) +  " " + str(fsize) + " " +  str(bsize) + " " +  str(len(self.paths[pathnumber].lastAcceptedFullTrajectory)) + " " + file)
       
        self.paths[pathnumber].shootingTime = self.paths[pathnumber].lastAcceptedFullTrajectory[rn][0]
        
        destfile = os.path.join(self.paths[pathnumber].nfsladir,dirnumber,"conforig.gro")
        shootfile = os.path.join(self.paths[pathnumber].nfsladir,dirnumber,"confshoot.gro")
        
        if os.path.exists(file):    
            self.filesystem.copyFiles(file,destfile)
        else:
            self.log.log.ERROR("File " + file + " not found, this is a fatal error")
        
        self.helper.shootVelocities(destfile,shootfile)
        
        for path in [self.paths[pathnumber],self.paths[pathnumber+1]]:
            self.filesystem.copyFiles(shootfile, os.path.join(path.workdir,"conf.gro"))
            path.finishedstate = -1
        
        if backwardpart:
            reversepath = pathnumber 
        else:
            reversepath = pathnumber + 1
        self.reverseBackwardGroFile(reversepath)
        
        self.log.log.info("shooting from " +str(rn)+ " file " + file + " backwardpart  " + str(backwardpart))
        
        self.filesystem.deleteFileList(fdir, "path*.gro")
        self.filesystem.deleteFileList(bdir, "path*.gro")
        
        
        
    def reverseBackwardGroFile(self,pathnumber):
        """
        Reverse all velocities from a gro file.
        """
        conffile = os.path.join(self.paths[pathnumber].workdir,"conf.gro")
        bakfile = os.path.join(self.paths[pathnumber].workdir,"bakconf.gro")
        bconffile = os.path.join(self.paths[pathnumber].workdir,"bconf.gro")
        self.helper.reverseVelocities(conffile, bconffile)
        self.filesystem.moveFile(conffile, bakfile)
        self.filesystem.moveFile(bconffile, conffile)


        
    def shootingQueue(self):
        """
        One of the main tps functions.
        Function that performes the mdrun on each of the paths.
        """
        
        """
        First step is to execute grompp in each of the paths workdirs to get a topol.tpr
        """
        for i in self.kernels.kernelPathsAll:
            workdir = self.paths[i].workdir
            os.chdir(workdir)
            ok = self.wrapper.checkInputFiles(self.paths[i].options, self.paths[i].options.initoptions,                         \
                                         ["-c","-p","-n"],workdir)
            self.log.log.debug(workdir + str(ok) + " grompp executed")
            self.paths[i].options.writeMdpFile(workdir,"md.mdp")
            
            cmd = self.wrapper.generateCommand(self.paths[i].options, self.paths[i].options.initoptions,                        \
                                          ["-c","-o","-p","-f","-n"],                                  \
                                          workdir,"grompp" )
            self.wrapper.executeCommand(cmd)
            os.chdir(self.basedir)
            
        """
        A process list is generated. It holds all the threads in a dictionary.
        The todo-list is the list of all processes that have to be executed.
        """
        processlist = {}
        todolist = self.kernels.kernelPathsAll[:]
        for i in range(self.cores-1):
            nextp = todolist.pop()
            os.chdir(self.paths[nextp].workdir)
            cmd =self.wrapper.generateMDRunCommand(self.paths[nextp].options, self.paths[nextp].workdir)
            processlist[nextp] = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.log.log.debug(str(todolist) + " " +  str(nextp) + "th thread started")
            
        finished = False
        """
        loop until all processes in the todo list are finished
        """
        while not(finished):    
            time.sleep(float(self.paths[0].options.runoptions["updatetime"]))
            finished = True
            for i in processlist.keys():
                #poll=None means it is still running
                if processlist[i].poll() == None:
                    finished = False
                    os.chdir(self.paths[i].workdir)
                    cmd = self.wrapper.generateGDistCommand(self.paths[i].workdir,self.paths[i].options)
                    self.wrapper.executeCommand(cmd, self.paths[i].options.runoptions["dist1"]+"\n"+self.paths[i].options.runoptions["dist2"]+"\n" )

                    if os.path.exists(os.path.join(self.paths[i].workdir,"dist.xvg")):
                        self.distparser.readDist(os.path.join(self.paths[i].workdir,"dist.xvg"))
                        
                        self.filesystem.deleteFileList(os.path.join(self.paths[i].workdir),"#*.xvg*")
                        #self.log.log.info(str(i) + " " + str(processlist[i].poll()) + " " + str(len(self.distparser.data)) + " " +  str(self.distparser.data[-1]))
                        pathfinished = self.paths[i].checkFinishedTPS(float(self.distparser.data[-1][self.stablestates.gdistDirection]),self.stablestates.states)
                        if pathfinished or len(self.distparser.data) > self.paths[i].options.runoptions["maxlength"]:
                            self.log.log.debug("Finished " + str(i) + " " + str(self.paths[i].finishedState))
                            processlist[i].terminate()
                            if len(todolist)>0:
                                nextp = todolist.pop()
                                os.chdir(self.paths[nextp].workdir)
                                cmd =self.wrapper.generateMDRunCommand(self.paths[nextp].options, self.paths[nextp].workdir)
                                processlist[nextp] = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                                self.log.log.debug(str(todolist) + " " +  str(nextp) + "th thread started")
        self.log.log.debug("Shooting is finished")
        
    
    def writeFinishedFiles(self,dirstring):
        for i in self.kernels.kernelPaths:
            lapath = self.paths[i].nfsladir
            newladir = os.path.join(lapath,dirstring)
            filename = os.path.join(newladir,"finished")
            of = open(filename,"w")
            of.write("finished")
            of.close()
            
    def finalizeShooting(self,dirstring):
        for i in self.kernels.kernelPathsAll:
            workdir = self.paths[i].workdir
            dest = os.path.join(workdir,"paths",dirstring)
            self.filesystem.createDir(dest)
            
            self.filesystem.moveFile(os.path.join(workdir,"traj.xtc"), dest)
            self.filesystem.moveFile(os.path.join(workdir,"traj.trr"), dest)
            self.filesystem.moveFile(os.path.join(workdir,"topol.tpr"), dest)
            self.filesystem.copyFiles(os.path.join(workdir,"index.ndx"), dest)
            self.filesystem.copyFiles(os.path.join(workdir,"conf.gro"), dest)
            self.filesystem.deleteFileList(workdir,"#*")
            self.filesystem.deleteFileList(workdir,"ener.edr")

    def deleteOldTrrFiles(self,dirnumber):
        dirlist = []
        for i in self.kernels.kernelPaths:
            dirlist.append(os.path.join(self.paths[i].nfsalldir,dirnumber,"forward"))
            dirlist.append(os.path.join(self.paths[i].nfsalldir,dirnumber,"backward"))
            dirlist.append(os.path.join(self.paths[i].nfsladir,dirnumber,"forward"))
            dirlist.append(os.path.join(self.paths[i].nfsladir,dirnumber,"backward"))
        
        for i in self.kernels.kernelPathsAll:
            mpath = self.paths[i]
            dirlist.append(os.path.join(mpath.workdir,"paths",dirnumber))
         
        for directory in dirlist:   
            self.filesystem.deleteFileList(directory,"*.trr")
    

    def checkAllTpsPathsAccepted(self):
        """
        This function updates the tpsaccepted variable
        """
        
        report = []
        for i in self.kernels.kernelPaths:
            self.getFullTrajectory(i,dirstring = "workdir")
            accepted = self.paths[i].checkAcceptedTPS(self.stablestates.states)
            self.paths[i].tpsaccepted = accepted
            self.paths[i+1].tpsaccepted = accepted
            report.append(str(accepted))
        self.log.log.info(" ".join(report))
        
                    
#
#    def updateCrossingHistos(self):
#        for i in self.kernels.kernelPaths:
#            maxv = self.paths[i].getMaxTrajectoryValue()
#            self.paths[i].crossingHisto.addToHisto(maxv)
#    
#    def outputAllCrossingHistos(self):
#        for i in self.kernels.kernelPaths:
#            filename = os.path.join(self.paths[i].nfsladir,"histo.txt")
#            self.paths[i].crossingHisto.outputCrossingHisto(filename)
    
    def finalizeTPS(self,dirstring,newdirstring):
        self.finalizeShooting(dirstring)
        acci = -1
        for i in self.kernels.kernelPaths:
            self.finalizeCopyLastAccepted(dirstring, newdirstring, i)
            if self.paths[i].tpsaccepted:
                acci=i
        if acci != -1:
            for i in self.kernels.kernelPaths:
                if not(self.paths[i].tpsaccepted):
                    self.finalizeCopyLastAcceptedFromTo(dirstring, newdirstring, acci,i)
    
    def finalizeCopyLastAccepted(self,dirstring,newdirstring,pathnumber):
        
        def _copyFiles(fromdir,destdir):
            self.filesystem.copyFiles(os.path.join(fromdir,"index.ndx"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"topol.tpr"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"traj.trr"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"traj.xtc"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"conf.gro"), destdir)
        
        lapath = self.paths[pathnumber].nfsladir
        newladir = os.path.join(lapath,newdirstring)
        newladirf = os.path.join(newladir,"forward")
        newladirb = os.path.join(newladir,"backward")
        
        allpath = self.paths[pathnumber].nfsalldir
        newalldir = os.path.join(allpath,newdirstring)
        newalldirf = os.path.join(newalldir,"forward")
        newalldirb = os.path.join(newalldir,"backward")
        dirlist = [allpath,lapath,newladir,newladirf,newladirb,newalldir,newalldirf,newalldirb]
        self.filesystem.createDirList(dirlist, self.log.log)
        
        fdir = os.path.join(self.paths[pathnumber].workdir,"paths",dirstring)
        bdir = os.path.join(self.paths[pathnumber+1].workdir,"paths",dirstring)
        
        if self.paths[pathnumber].tpsaccepted:
            _copyFiles(fdir, newladirf)
            _copyFiles(bdir, newladirb)
             
            self.paths[pathnumber].lastAcceptedFullTrajectory = self.paths[pathnumber].fullTrajectory[:]
            self.paths[pathnumber].lastAcceptedFullTrajectoryblength = self.paths[pathnumber].fullTrajectoryblength
            self.paths[pathnumber].lastAcceptedFullTrajectoryflength = self.paths[pathnumber].fullTrajectoryflength           

        else:
            oldladir = os.path.join(lapath,dirstring)
            fdir = os.path.join(oldladir,"forward")
            bdir = os.path.join(oldladir,"backward")
            
            _copyFiles(fdir, newladirf)
            _copyFiles(bdir, newladirb)
        

    def finalizeCopyLastAcceptedFromTo(self,dirstring,newdirstring,pathnumber,to):
        
        def _copyFiles(fromdir,destdir):
            self.filesystem.copyFiles(os.path.join(fromdir,"index.ndx"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"topol.tpr"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"traj.trr"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"traj.xtc"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"conf.gro"), destdir)
            
        
        lapath = self.paths[to].nfsladir
        newladir = os.path.join(lapath,newdirstring)
        newladirf = os.path.join(newladir,"forward")
        newladirb = os.path.join(newladir,"backward")
        
        dirlist = [lapath,newladir,newladirf,newladirb]
        self.filesystem.createDirList(dirlist, self.log.log)
        
        fdir = os.path.join(self.paths[pathnumber].workdir,"paths",dirstring)
        bdir = os.path.join(self.paths[pathnumber+1].workdir,"paths",dirstring)
        
        _copyFiles(fdir, newladirf)
        _copyFiles(bdir, newladirb)
             
    
    def getFullTrajectory(self,pathnumber,dirstring):
        if dirstring == "workdir":
            fdir = self.paths[pathnumber].workdir
            bdir = self.paths[pathnumber+1].workdir
        else:
            fdir = os.path.join(self.paths[pathnumber].nfsladir,dirstring,"forward")
            bdir = os.path.join(self.paths[pathnumber].nfsladir,dirstring,"backward")
        
        traj = []
        
        os.chdir(bdir)
        cmd = self.wrapper.generateGDistCommand(bdir,self.paths[pathnumber].options)
        self.wrapper.executeCommand(cmd, self.paths[pathnumber].options.runoptions["dist1"]+"\n"+self.paths[pathnumber].options.runoptions["dist2"]+"\n" )

        self.distparser.readDist(os.path.join(bdir,"dist.xvg"))
        self.filesystem.deleteFile(os.path.join(bdir,"dist.xvg"))
        #totaltime = float(self.distparser.data[-1][1])
        self.distparser.data.reverse()
        self.paths[pathnumber].fullTrajectoryblength=0
        count = 0
        for line in self.distparser.data:
            traj.append([count,float(line[self.stablestates.gdistDirection]),0])
            self.paths[pathnumber].fullTrajectoryblength+=1
            count += 1
        
        os.chdir(fdir)
        cmd = self.wrapper.generateGDistCommand(fdir,self.paths[1].options)
        self.wrapper.executeCommand(cmd, self.paths[1].options.runoptions["dist1"]+"\n"+self.paths[1].options.runoptions["dist2"]+"\n" )

        self.distparser.readDist(os.path.join(fdir,"dist.xvg"))
        self.filesystem.deleteFile(os.path.join(bdir,"dist.xvg"))
        self.paths[pathnumber].fullTrajectoryflength=0
        for line in self.distparser.data[1:]:
            traj.append([count,float(line[self.stablestates.gdistDirection]),1])
            self.paths[pathnumber].fullTrajectoryflength+=1
            count += 1
        
        for i in range(len(traj)):
            traj[i][0] = traj[i][0] - self.paths[pathnumber].fullTrajectoryblength + self.paths[pathnumber].shootingTime
        self.log.log.debug( "path blength shootingtime" + str(pathnumber) + " " + str(self.paths[pathnumber].fullTrajectoryblength) + " " + str(self.paths[pathnumber].shootingTime))
        self.paths[pathnumber].fullTrajectory = traj[:]
        self.paths[pathnumber+1].fullTrajectory = traj[:]
        
   
    def _outputFullTrajectory(self,directory,pathnumber,dirstring):
        of = open(os.path.join(directory,"trajectoryZ."+dirstring+".dat"),"w")
        for position in self.paths[pathnumber].fullTrajectory:
            of.write("%d %.18f %d\n" % (position[0],position[1],position[2]))
        of.close()

        of = open(os.path.join(directory,"trajectoryZ."+dirstring+".acc"),"w")
        for position in self.paths[pathnumber].lastAcceptedFullTrajectory:
            of.write("%d %.18f %d\n" % (position[0],position[1],position[2]))
        of.close()
    
    
    def outputAllFullTrajectories(self,dirstring):
        for i in self.kernels.kernelPaths:
            ladir = os.path.join(self.paths[i].nfsladir,dirstring)
            self._outputFullTrajectory(ladir, i,dirstring)
            

    def readLastAcceptedTrajectories(self,dirstring):
        for i in self.kernels.kernelPaths:
            ladir = os.path.join(self.paths[i].nfsladir,dirstring)
            self._readFullTrajectory(ladir, i,dirstring)
        
    
    def _readFullTrajectory(self,directory,pathnumber,dirstring):
        traj = []
        self.paths[pathnumber].lastAcceptedFullTrajectoryblength = 0
        self.paths[pathnumber].lastAcceptedFullTrajectoryflength = 0
        
        for line in open(os.path.join(directory,"trajectoryZ."+dirstring+".acc"),"r"):
            raw = line.split()
            traj.append([int(float(raw[0])),float(raw[1]),int(float(raw[2]))])
            self.paths[pathnumber].lastAcceptedFullTrajectory = traj[:]
            self.paths[pathnumber+1].lastAcceptedFullTrajectory = traj[:]
            if int(float(raw[2])) == 0:
                self.paths[pathnumber].lastAcceptedFullTrajectoryblength += 1
            else:
                self.paths[pathnumber].lastAcceptedFullTrajectoryflength += 1
    
    def _copyLastAcceptedToFull(self,pathnumber):
        self.paths[pathnumber].fullTrajectoryblength = self.paths[pathnumber].lastAcceptedFullTrajectoryblength
        self.paths[pathnumber].fullTrajectoryflength = self.paths[pathnumber].lastAcceptedFullTrajectoryflength
        self.paths[pathnumber].fullTrajectory = self.paths[pathnumber].lastAcceptedFullTrajectory[:]
        
                        