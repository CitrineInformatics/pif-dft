from .base import DFTParser
import os
from ase.calculators.vasp import Vasp

class VaspParser(DFTParser):
    """
    Parser for VASP calculations
    """
    
    def get_name(self): return "VASP"
    
    def test_if_from(self, directory):
        # Check whether it has an INCAR file
        return os.path.isfile(os.path.join(directory, 'INCAR'))
        
        
    def get_cutoff_energy(self):
        # Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        
        # Look for ENCUT
        for line in fp:
            if "ENCUT" in line:
                words = line.split()
                return (float(words[2]),words[3])
                
        # Error handling: ENCUT not found
        raise Exception('ENCUT not found')
