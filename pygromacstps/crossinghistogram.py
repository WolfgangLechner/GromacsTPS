'''
Created on June 16, 2010

@author: wolf
'''

import numpy as np

class generichistogram(object):
    """
    A Crossing histogram can be based on a trajectory either forward or backward in time
    histomin is the position of the interface and histomax can be chosen arbitrarily
    """
    def __init__(self,histosize=2000,histomin=-4.0,histomax=4.0,forward=True):
        self.histo = np.zeros(histosize)
        self.histomin = histomin
        self.histomax = histomax
        self.histosize = histosize
        self.norm = 0.0
        self.forward = forward
    
    def _getBox(self,value):
        """
        Convert the value to the histogrambox
        """
        return (float(self.histosize)*(float(value) - float(self.histomin)))/(float(self.histomax-self.histomin))
    
    def _getValue(self,hbox):
        """
        Convert the histogram index to the according value
        """
        return (float(hbox)*float(self.histomax-self.histomin) )/float(self.histosize) + float(self.histomin)
    
         
    def addRangeToHisto(self,value):
        """
        Add the value 1 in the range from value to histomax
        """
        hbox = int(round(self._getBox(value)))
        if self.forward:
            if hbox > self.histosize - 1:
                hbox = self.histosize -1
            for i in range(int(hbox)):
                self.histo[i] += 1.0
        else:
            if hbox < 0:
                hbox = 0
            for i in range(self.histosize-int(hbox)):
                self.histo[self.histosize-i-1] += 1.0
        self.norm += 1.0
    
        
    def addPointToHisto(self,value):
        """
        Add a single point to the histogram
        """
        hbox = int(round(self._getBox(value)))
        self.histo[hbox] += 1.0
        self.norm += 1.0
    
        
    
    def outputCrossingHisto(self,filename):
        """
        Print the histogram
        """
        of = open(filename,"w")
        for i in range(self.histosize):
            of.write("%.18f %.18f\n" % (self._getValue(i),self.histo[i]/self.norm))
        of.close()
    
    
    