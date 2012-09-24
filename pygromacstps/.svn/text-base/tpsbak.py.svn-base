'''
Created on May 3, 2010

@author: Wolfgang Lechner
'''


import wrappers
import parser
import pathsimulation
import filesystem
import gtpslogging
import interfaces
import stablestates
import helpers
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
    def __init__(self,basedir=".",mode="initial",cores=-1):
        self.basedir = basedir
        self.mode = mode
        self.lastAcceptedPath = "start"
        if cores == -1:
            self.cores = multiprocessing.cpu_count()
        else:
            self.cores = cores
        self.wrapper = wrappers.gromacswrapper()
        self.distparser = parser.gdistparser()
        self.filesystem = filesystem.filesystem()
        self.interfaces = interfaces.interfaces()
        self.stablestates = stablestates.stablestates()
        self.helper = helpers.helpers()
        #Initialize the logger
        self.log = gtpslogging.log("debug",basedir)
        self.log.log.debug("logfile created")
        self.log.log.info(str(self.cores) + " CPUs detected")
        
        #read the stables states from a file
        self.stablestates.readStates(os.path.join(basedir,"stablestates.txt"))
        self.log.log.info("Read States : " + str(self.stablestates.states))
        
        """
        This array holds all the information about the paths. Each trajectory consists of a 
        forward-part and a backward-part. The trajectory can either be a forward trajectory
        or a backward trajectory. Forward trajectroies start in A.
        """
        self.paths = []
        self.paths.append(pathsimulation.pathdata(0,basedir,mode,forward=True,forwardpart=True))
        self.paths.append(pathsimulation.pathdata(0,basedir,mode,forward=True,forwardpart=False))
        
    
    def preperationFromStart(self,copyfiles = True):
        """
        Creating the directory structure and copying standardfiles there, given that copyfile = True
        """
        for i in range(len(self.paths)):
            workdir = self.paths[i].workdir
            
            initdir = self.paths[i].options.paths["initialpath"]
            self.filesystem.createDir(self.paths[i].baseworkdir)
            self.filesystem.createDir(self.paths[i].workdir)
            self.log.log.debug(self.paths[i].workdir + " created")
            
            self.filesystem.createDir(workdir)
            self.log.log.debug(workdir + " created")
            
            self.filesystem.createDir(workdir)
            self.log.log.debug(workdir + " created")
            
            self.filesystem.createDir(os.path.join(workdir,'paths'))
            self.log.log.debug(os.path.join(workdir,'paths') + " created")
            
            if copyfiles:  
                for file in self.paths[i].options.standardfiles:
                    self.filesystem.copyFiles(os.path.join(initdir,"standardfiles",file), workdir)
            

    def preperationTPS(self,copyfiles = True):
        """
        Creating the directory structure and copying standardfiles there, given that copyfile = True
        """
        for i in range(len(self.paths)):
            workdir = self.paths[i].workdir
            
            initdir = self.paths[i].options.paths["initialpath"]
            self.filesystem.createDir(initdir)
            self.filesystem.createDir(os.path.join(initdir,"la"))

            
            self.filesystem.createDir(self.paths[i].baseworkdir)
            self.filesystem.createDir(self.paths[i].workdir)
            self.filesystem.createDir(self.paths[i].ladir)
            self.filesystem.createDir(os.path.join(self.paths[i].ladir,"start"))
            self.filesystem.createDir(os.path.join(self.paths[i].ladir,"start/forward"))
            self.filesystem.createDir(os.path.join(self.paths[i].ladir,"start/backward"))
            
            self.log.log.debug(self.paths[i].workdir + " created")
            
            self.filesystem.createDir(workdir)
            self.log.log.debug(workdir + " created")
            
            self.filesystem.createDir(workdir)
            self.log.log.debug(workdir + " created")
            
            self.filesystem.createDir(os.path.join(workdir,'paths'))
            self.log.log.debug(os.path.join(workdir,'paths') + " created")
            
            if copyfiles:  
                for file in self.paths[i].options.standardfiles:
                    self.filesystem.copyFiles(os.path.join(initdir,"standardfiles",file), workdir)
            
    def lastAcceptedToGro(self,dirnumber):
        """
        The last accepted trajectory is transformed into gro files using trjconv. 
        """
        workdir = os.path.join(self.paths[0].ladir,dirnumber,"forward")
        cmd = self.wrapper.generateTrjconvCommand(self.paths[0].options,workdir,workdir)
        self.wrapper.executeCommand(cmd, tinput="0")
        
        workdir = os.path.join(self.paths[0].ladir,dirnumber,"backward")
        cmd = self.wrapper.generateTrjconvCommand(self.paths[0].options,workdir,workdir)
        self.wrapper.executeCommand(cmd, tinput="0")
    
    def pickConfigurationLastAccepted(self,dirnumber):
        """
        A random configuration is taken from a trajectory and the shooting move is performed.
        and copy the files to the workdir of the path.
        """
        fdir = os.path.join(self.paths[0].ladir,dirnumber,"forward")
        flist = self.filesystem.getFileList(fdir, "path*.gro")
        fsize = len(flist)
        bdir = os.path.join(self.paths[0].ladir,dirnumber,"backward")
        blist = self.filesystem.getFileList(bdir, "path*.gro")
        bsize = len(blist)
        sum = fsize + bsize
        rn = random.randint(0,sum-1)
        forwardpart = (rn < fsize)
        if forwardpart:
            file = os.path.join(fdir,"path%d.gro" % (rn))
        else:
            file = os.path.join(bdir,"path%d.gro" % (rn-fsize))
        
        destfile = os.path.join(self.paths[0].ladir,dirnumber,"conforig.gro")
        shootfile = os.path.join(self.paths[0].ladir,dirnumber,"confshoot.gro")
        
        if os.path.exists(file):    
            self.filesystem.copyFiles(file,destfile)
        else:
            self.log.log.ERROR("File " + file + " not found, this is a fatal error")
        
        self.helper.shootVelocities(destfile,shootfile )
        
        for path in self.paths:
            self.filesystem.copyFiles(shootfile, os.path.join(path.workdir,"conf.gro"))
            path.finishedstate = -1
            
        
        reversepath = forwardpart and 1 or 0
        self.reverseBackwardGroFile(reversepath)
        
        self.log.log.info("shooting from " +dirnumber+ " file " + file + " forwardpart " + str(forwardpart))
        
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

    def shootingGroFile(self):
        """
        Perform a shooting move on a gro file.
        """
        conffile = os.path.join(self.paths[0].workdir,"conf.gro")
        bakfile = os.path.join(self.paths[0].workdir,"bakconf.gro")
        bconffile = os.path.join(self.paths[0].workdir,"bconf.gro")
        self.helper.shootVelocities(conffile, bconffile)  
        self.filesystem.moveFile(conffile, bakfile)
        self.filesystem.moveFile(bconffile, conffile)
        dest = self.paths[1].workdir
        self.filesystem.copyFiles(conffile, dest)
        self.reverseBackwardGroFile(1)
    
    def shootingQueue(self):
        """
        One of the main tps functions.
        Function that performes the mdrun on each of the paths.
        """
        
        """
        First step is to execute grompp in each of the paths workdirs to get a topol.tpr
        """
        for i in range(len(self.paths)):
            workdir = self.paths[i].workdir
            ok = self.wrapper.checkInputFiles(self.paths[i].options, self.paths[i].options.initoptions,                         \
                                         ["-c","-p","-n"],workdir)
            self.log.log.debug(workdir + str(ok) + " grompp executed")
            self.paths[i].options.writeMdpFile(workdir,"md.mdp")
            
            cmd = self.wrapper.generateCommand(self.paths[i].options, self.paths[i].options.initoptions,                        \
                                          ["-c","-o","-p","-f","-n"],                                  \
                                          workdir,"grompp" )
            self.wrapper.executeCommand(cmd)
            
        """
        A process list is generated. It holds all the threads in a dictionary.
        The todo-list is the list of all processes that have to be executed.
        """
        processlist = {}
        todolist = range(len(self.paths))
        nextp = todolist.pop()
        for i in range(self.cores-1):
            os.chdir(self.paths[nextp].workdir)
            cmd =self.wrapper.generateMDRunCommand(self.paths[nextp].options, self.paths[nextp].workdir)
            processlist[nextp] = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.log.log.debug(str(todolist) + " " +  str(nextp) + "th thread started")
        
        finished = False
        """
        loop until all processes in the todo list are finished
        """
        while not(finished):    
            time.sleep(self.paths[0].options.runoptions["updatetime"])
            finished = True
            for i in processlist.keys():
                #poll=None means it is still running
                if processlist[i].poll() == None:
                    finished = False
                    os.chdir(self.paths[i].workdir)
                    cmd = self.wrapper.generateGDistCommand(self.paths[i].workdir,self.paths[i].options)
                    self.wrapper.executeCommand(cmd, "1\n3\n" )
                    self.distparser.readDist(os.path.join(self.paths[i].workdir,"dist.xvg"))
                    self.log.log.info(str(i) + " " + str(processlist[i].poll()) + " " + str(len(self.distparser.data)) + " " +  str(self.distparser.data[-1]))
                    pathfinished = self.paths[i].checkFinished(float(self.distparser.data[-1][self.stablestates.gdistDirection]),self.stablestates.states)
                    if pathfinished or len(self.distparser.data) > self.paths[i].options.runoptions["maxlength"]:
                        self.log.log.debug("Finished " + str(i) + " " + str(self.paths[i].finishedState))
                        processlist[i].terminate()
                        if len(todolist)>0:
                            nextp = todolist.pop()
                            os.chdir(self.paths[nextp].workdir)
                            cmd =self.wrapper.generateMDRunCommand(self.paths[nextp].options, self.paths[nextp].workdir)
                            processlist[nextp] = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                            self.log.log.debug(str(todolist) + " " +  str(nextp) + "th thread started")
        self.log.log.debug("Shooting went well")
        
    def finalizeShooting(self,dirnumber):
        for i in range(len(self.paths)):
            workdir = self.paths[i].workdir
            #cmd = self.wrapper.generateTrjconvCommand(self.paths[i].options,workdir,os.path.join(workdir))
            #self.wrapper.executeCommand(cmd,"0")
            
            dest = os.path.join(workdir,"paths",dirnumber)
            self.filesystem.createDir(dest)
            #self.filesystem.copyFileList(workdir, dest, "path*.gro")
            #self.filesystem.copyFileList(workdir, dest, "traj.xtc")
            #self.filesystem.copyFileList(workdir, dest, "conf.gro")
            self.filesystem.moveFile(os.path.join(workdir,"traj.xtc"), dest)
            self.filesystem.moveFile(os.path.join(workdir,"traj.trr"), dest)
            self.filesystem.moveFile(os.path.join(workdir,"topol.tpr"), dest)
            self.filesystem.copyFiles(os.path.join(workdir,"index.ndx"), dest)
            self.filesystem.copyFiles(os.path.join(workdir,"conf.gro"), dest)
            self.filesystem.deleteFileList(workdir,"#*")
            self.filesystem.deleteFileList(workdir,"ener.edr")

        
    def finalizeCopyLastAccepted(self,dirnumber):
        
        def _copyFiles(fromdir,destdir):
            self.filesystem.copyFiles(os.path.join(fromdir,"index.ndx"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"topol.tpr"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"traj.trr"), destdir)
            self.filesystem.copyFiles(os.path.join(fromdir,"traj.xtc"), destdir)
        
        lapath = self.paths[0].ladir
        newladir = os.path.join(lapath,dirnumber)
        newladirf = os.path.join(newladir,"forward")
        newladirb = os.path.join(newladir,"backward")
        
        allpath = self.paths[0].alldir
        newalldir = os.path.join(allpath,dirnumber)
        newalldirf = os.path.join(newalldir,"forward")
        newalldirb = os.path.join(newalldir,"backward")
        
        self.filesystem.createDir(allpath)
        self.filesystem.createDir(lapath)
        self.filesystem.createDir(newladir)
        self.filesystem.createDir(newladirf)
        self.filesystem.createDir(newladirb)
        self.filesystem.createDir(newalldir)
        self.filesystem.createDir(newalldirf)
        self.filesystem.createDir(newalldirb)
        
        
        pathaccepted = self.paths[0].finishedState == 1 and self.paths[1].finishedState == 4
        if pathaccepted:
            fdir = os.path.join(self.paths[0].workdir,"paths",dirnumber)
            bdir = os.path.join(self.paths[1].workdir,"paths",dirnumber)
            
            _copyFiles(fdir, newladirf)
            _copyFiles(bdir, newladirb)
            
            self.lastAcceptedPath = dirnumber
        else:
            lapath = self.paths[0].ladir
            oldladir = os.path.join(lapath,self.lastAcceptedPath)
            fdir = os.path.join(oldladir,"forward")
            bdir = os.path.join(oldladir,"backward")
            _copyFiles(fdir, newladirf)
            _copyFiles(bdir, newladirb)
        
        _copyFiles(fdir, newalldirf)
        _copyFiles(bdir, newalldirb)

    
    def getFullTrajectory(self,lastaccepted,dirnumber):
        if lastaccepted:
            ladir = os.path.join(self.paths[0].ladir,dirnumber)
        else:
            ladir = os.path.join(self.paths[0].alldir,dirnumber)
        
        fdir = os.path.join(ladir,"forward")
        bdir = os.path.join(ladir,"backward")
        traj = []
        
            
        os.chdir(bdir)
        cmd = self.wrapper.generateGDistCommand(bdir,self.paths[0].options)
        self.wrapper.executeCommand(cmd, "1\n3\n" )
        self.distparser.readDist(os.path.join(bdir,"dist.xvg"))
        totaltime = float(self.distparser.data[-1][1])
        self.distparser.data.reverse()
        for line in self.distparser.data:
            traj.append([totaltime - float(line[1]),float(line[self.stablestates.gdistDirection])])
        
        os.chdir(fdir)
        cmd = self.wrapper.generateGDistCommand(fdir,self.paths[1].options)
        self.wrapper.executeCommand(cmd, "1\n3\n" )
        self.distparser.readDist(os.path.join(fdir,"dist.xvg"))
        for line in self.distparser.data:
            traj.append([float(line[1])+totaltime,float(line[self.stablestates.gdistDirection])])
        
        of = open(os.path.join(ladir,"trajectoryZ.dat"),"w")
        for line in traj:
            of.write("%.18f %.18f\n" % (line[1],line[0]))
        of.close()
        
        return traj
            
            
            
            
            
