from .base import DFTParser
import os
from ase.calculators.vasp import Vasp

class VaspParser(DFTParser):
    """
    Parser for VASP calculations
    """
    
    def get_name(): return "VASP"
    
    def test_if_from(self, directory):
        # Check whether it has an INCAR file
        return os.path.isfile(os.path.join(directory, 'INCAR'))
        
