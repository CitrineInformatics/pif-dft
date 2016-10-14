from pypif.obj.common.property import Property

from .base import DFTParser, Value_if_true
import os
from pypif.obj.common.value import Value

class PwscfParser(DFTParser):
    '''
    Parser for PWSCF calculations
    '''
    
    def get_name(self): return "PWSCF"
    
    def test_if_from(self,directory):
        '''Look for PWSCF input and output files'''
        self.inputf=self.outputf=''
        maxlines=15
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        for f in files:
            fp = open(os.path.join(directory, f), 'r')
            for l in range(maxlines):
                line = fp.readline()
                if "Program PWSCF" in line:
                    fp.close()
                    self.outputf = f
                    break
                elif "&control" in line.lower():
                    fp.close()
                    self.inputf = f
                    break
            fp.close()
            if self.inputf and self.outputf: return True
        return False

    def get_xc_functional(self):
        '''Determine the xc functional'''
        # grab Exchange-correlation line in outputf
        # the xc functional is described by 4 strings
        # special case: just 1 string (e.g. PBE)
        # Examples:
        # SLA  PZ   NOGX NOGC ( 1 1 0 0 0)
        # SLA  PW   PBE  PBE ( 1  4  3  4 0 0)
        # SLA  PW   TPSS TPSS (1476)
        # SLA  PW   PBX  PBC (1434)
        # PBE ( 1  4  3  4 0 0)
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "Exchange-correlation" in line:
                    xcstring = line.split()[2:6]
                    for word in range(4):
                        if xcstring[word][0] == '(':
                            xcstring=xcstring[:word]
                            break
                    return Value(scalars=" ".join(xcstring))
            raise Exception('xc functional not found')
