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
        #store the number of atoms and number of irreducible K-points
        for line in fp:
            if "NIONS" in line:
                words = line.split()
                NI = int(words[11])
            elif "NKPTS" in line:
                words = line.split()
                NIRK = float(words[3])
        #check if the number of k-points was reduced by VASP if so, sum all the k-points weight
        if "irreducible" in open(os.path.join(self._directory, 'OUTCAR')).read():
            fp.seek(0)
            for line in fp:
                #sum all the k-points weight
                if "Coordinates               Weight" in line:
                    NK=0; counter = 0
                    for line in fp:
                        if counter == NIRK:
                            break
                        NK += float(line.split()[3])
                        counter += 1
            return (NI*NK)
        #if k-points were not reduced KPPRA equals the number of atoms * number of irreducible k-points
        else:
            return(NI*NIRK)

                
        # Error handling: NKPTS or NIONS not found
        raise Exception('NIONS, irredicuble or Coordinates not found')

    def _is_converged(self):
        return self._call_ase(Vasp().read_convergence)
        
    def get_total_energy(self):
        return (self._call_ase(Vasp().read_energy)[0], 'eV')

    def get_version_number(self):
        # Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        
        #look for vasp
        for line in fp:
            if "vasp" in line:
                words = line.split()
                return (words[0].strip('vasp.'))
                break
        
        # Error handling: vasp not found
        raise Exception('vasp not found')
        
    def get_U_settings(self):
        #Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        #Check if U is used
        if "LDAU" in open(os.path.join(self._directory, 'OUTCAR')).read():
            U_param = {}
            atoms = []
            #get the list of pseupotential used
            for line in fp:
                if "TITEL" in line:
                    atoms.append(line.split()[3])
                #Get the U type used
                if "LDAUTYPE" in line:
                        U_param['U-type'] = int(line.split()[-1])
            atoms.reverse()
            fp.seek(0)
            #Get the L value            
            for line in fp:
                for atom, i in zip(atoms, range(len(atoms))):
                    if "LDAUL" in line:
                            U_param[atom] = {'L': int(line.split()[-1-i])}
            fp.seek(0)
            #Get the U value            
            for line in fp:
                for atom, i in zip(atoms, range(len(atoms))):
                    if "LDAUU" in line:
                            U_param[atom]['U'] = float(line.split()[-1-i])
            fp.seek(0)
            #Get the J value
            for line in fp:
                for atom, i in zip(atoms, range(len(atoms))):
                    if "LDAUJ" in line:
                            U_param[atom]['J'] = float(line.split()[-1-i])
            return (U_param)
        #if U is not used, return None
        else:
            return (None)
            
    def get_vdW_settings(self):
        #define the name of the vdW methods in function of their keyword
        vdW_dict = {'BO':'optPBE-vdW', 'MK':'optB88-vdW', 'ML':'optB86b-vdW','RE':'vdW-DF','OR':'Klimes-Bowler-Michaelides'}
        #Open up the OUTCAR
        fp = open(os.path.join(self._directory, 'OUTCAR'), 'r')
        #Check if vdW is used
        if "LUSE_VDW" in open(os.path.join(self._directory, 'OUTCAR')).read():
            #if vdW is used, get its keyword             
            for line in fp:
                if "GGA     =" in line:
                    words = line.split()
                    return (vdW_dict[words[2]])
        #if vdW is not used, return None
        else:
            return (None)
            
    def get_pressure(self):
        #define pressure dictionnary because since when is kB = kbar? Come on VASP people
        pressure_dict = {'kB':'kbar'}
        #Check if ISIF = 0 is used
        if "ISIF   =      0" in open(os.path.join(self._directory, 'OUTCAR')).read():
            #if ISIF = 0 is used, print this crap
            return ("Pressure not calculated (ISIF = 0)")
        #if ISIF is not 0 then extract pressure and units
        else:
            #scan file in reverse to have the final pressure
            for line in reversed(open(os.path.join(self._directory, 'OUTCAR')).readlines()):
                if "external pressure" in line:
                    words = line.split()
                    return (float(words[3]), pressure_dict[words[4]])
                    break
                    
                    
                
        
        
                    
        
        
