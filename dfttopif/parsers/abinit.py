from .base import DFTParser
import os
import glob
from ase.calculators.abinit import Abinit
from pypif.obj.common import Value, Property

class AbinitParser(DFTParser):
    '''
    Parser for ABINIT calculations
    '''
    _label = None
    
    def get_name(self): return "ABINIT"
    
    def test_if_from(self, directory):
        # Check whether any file has as name ABINIT in the file in the first two lines
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        for f in files:
            fp = open(os.path.join(directory, f), 'r')
            for line in [fp.readline(), fp.readline()]:
                if "ABINIT" in line:
                    fp.close()
                    return True
            fp.close()
        return False
        
    def _get_label(self):
        '''Find the label for the output files 
         for this calculation
        '''
        if self._label is None:
            files = [f for f in os.listdir(self._directory) if os.path.isfile(os.path.join(self._directory, f))] 
            foundfiles = False
            print(files)
            for f in files:
                if ".files" in f: 
                    foundfiles = True
                    self._label = f.split(".")[0]
                    fp = open(os.path.join(self._directory, self._label + '.files'), 'r')
                    line = fp.readline().split()[0]
                    if line != self._label + ".in":
                       fp.close()
                       raise Exception('first line must be label.in') 
                    line = fp.readline().split()[0]
                    if line != self._label + ".txt":
                       fp.close()
                       raise Exception('second line must be label.txt') 
                    line = fp.readline().split()[0]
                    if line != self._label + "i":
                       fp.close()
                       raise Exception('third line must be labeli') 
                    line = fp.readline().split()[0]
                    if line != self._label + "o":
                       fp.close()
                       raise Exception('fourth line must be labelo') 
                    fp.close()
            if foundfiles:
                return self._label
            else:
                raise Exception('label.files not found')
                                
#ASE format
#        (self.prefix + '.in') # input
#        (self.prefix + '.txt')# output
#        (self.prefix + 'i')   # input
#        (self.prefix + 'o')   # output
                
        else:
            return self._label

    def get_cutoff_energy(self):
        # Open up the label.txt file
        fp = open(os.path.join(self._directory, self._label + '.out'), 'r')
        foundecho = False 
        # Look for ecut after the occurence of "echo values of preprocessed input variables"
        for line in fp:
            if "echo values of preprocessed input variables" in line:
                foundecho = True
            if "ecut" in line and foundecho:
                words = line.split()
                return Value(scalars=float(words[1]), units=words[2])
        # Error handling: ecut not found
        raise Exception('ecut not found')
