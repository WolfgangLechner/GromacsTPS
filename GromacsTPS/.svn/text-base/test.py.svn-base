'''
Created on May 6, 2010

@author: wolf
'''
import subprocess
import sys
import os
import time
ospath = "/Users/wolf/work/projects/membranes/python/GromacsTPS/run/dopcval/initial/0/"
gpath = "/Users/wolf/localApps/gromacs/bin/"

os.chdir(ospath)
p = subprocess.Popen([gpath+'mdrun'], stdout = subprocess.PIPE,stderr=subprocess.PIPE)

print "hello"

time.sleep(2)

p.terminate()