from pypif.obj.common.property import Property

from .base import DFTParser, Value_if_true
import os
from pypif.obj.common.value import Value

class PwscfParser(DFTParser):
    '''
    Parser for PWSCF calculations
    '''
    
    def get_name(self): return "PWSCF"
    
    def test_if_from(self, directory):
        # Check whether any file in the directory contains Program
        # PWSCF in the first maxlines lines
        maxlines=15
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        for f in files:
            fp = open(os.path.join(directory, f), 'r')
            for l in range(maxlines):
                line = fp.readline()
                if "Program PWSCF" in line:
                    fp.close()
                    return True
            fp.close()
        return False
