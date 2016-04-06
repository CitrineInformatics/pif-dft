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

    def uses_SOC(self):
        # Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        
        #look for LSORBIT
        for line in fp:
            if "LSORBIT" in line:
                words = line.split()
                return (words[2] == 'T')
        
        # Error handling: LSORBIT not found
        raise Exception('LSORBIT not found')
        
    def is_relaxed(self):
        # Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        
        # Look for NSW
        for line in fp:
            if "NSW" in line:
                words = line.split()
                return (int(words[2]) != 0)
                
        # Error handling: NSW not found
        raise Exception('NSW not found')
        
    def get_xc_functional(self):
        # Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        
        # Look for TITEL
        for line in fp:
            if "TITEL" in line:
                words = line.split()
                return (words[2])
                break
            
    def get_pp_name(self):
        # Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        
        #initialize empty list to store pseudopotentials
        pp = []
        # Look for TITEL
        for line in fp:
            if "TITEL" in line:
                words = line.split()
                pp.append(words[3])
        return (pp)
                
        # Error handling: TITEL not found
        raise Exception('TITEL not found')
        
    def get_KPPRA(self):
        # Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        
        # Look for NKPTS and NIONS
        for line in fp:
            if "NKPTS" in line:
                words = line.split()
                NK = int(words[3])
            elif "NIONS" in line:
                words = line.split()
                NI = int(words[11])
        return (NK*NI)
                
        # Error handling: NKPTS or NIONS not found
        raise Exception('NKPTS or NIONS not found')

    def _is_converged(self):
        return self._call_ase(Vasp().read_convergence)
        
    def get_total_energy(self):
        return (self._call_ase(Vasp().read_energy)[0], 'eV')

