import os
from collections import Counter


class DFTParser:
    '''
    Base class for all tools to parse a directory
    of output files from a DFT Calculation
    
    To use this class, provide the path to a directory
    to containing the output files from a DFT calculation.
    Once instantiated, call the methods provided by this
    class in order to retrieve the settings and results
    of the calculation.
    
    To get a list of names of the settings available for this
    a particular instance, call get_setting_functions()
    
    To get a list of the names of results available via
    a particular instance, call  get_result_functions()

    Developer Notes
    ---------------
    
    Settings and properties should return None if not 
    not available, or not implemented
    '''
    
    _directory = None
    '''Path to directory containing calculation files'''
    
    _converged = None
    ''' Whether this calculation has converged '''
    
    def __init__(self, directory):
        '''Intialize a parser. 
        
        Input:
            directory - String, path to a directory of output files
        '''
        
        # Sanity check: Make sure the format is correct
        if not self.test_if_from(directory):
            raise Exception('Files in directory inconsistant with this format')
            
        self._directory = directory
      
    @classmethod
    def test_if_from(self, directory):
        '''Test whether a directory of output files
        seems like it is from this DFT code.
        
        Input:
            directory - String, path to a directory of output files
        Returns: 
            boolean, whether directory was created by this code
        '''
        
        raise NotImplementedError
        
    def get_setting_functions(self):
        '''Get a dictionary containing the names of methods
        that return settings of the calculation
        
        Returns:
            dict, where the key is the name of the setting,
                and the value is a tuple containing
                (
                    [Function name for this parser],
                    [Data Type (None,Scalar,Vector,Matrix,Tag)]
                )
        '''
        return {
            'XC Functional':('get_xc_functional','tag'),
            'Relaxed':('is_relaxed',None),
            'Cutoff Energy':('get_cutoff_energy','scalar'),
            'k-Points per Reciprocal Atom':('get_KPPRA','scalar'),
            'Spin-Orbit Coupling':('uses_SOC', None),
            'DFT+U':('get_U_settings', 'tag'),
            'vdW Interactions':('get_vdW_settings','tag'),
            'Psuedopotentials':('get_pp_name','tag'),
        }
        
    def get_result_functions(self):
        '''Get a dictionary describing the names of methods 
        that return results of the calculation
        
        Returns:
            dict, where the key is the name of a problem,
                and the value is a tuple containing
                (
                    [Function name for this parser],
                    [Data Type (None,Scalar,Vector,Matrix,Tag)]
                )
        '''
        return {
            'Converged':('is_converged', 'none'),
            'Total Energy':('get_total_energy', 'scalar'),
            'Band Gap Energy':('get_band_gap', 'scalar'),
            'Pressure':('get_pressure', 'scalar'),
        }
        
    def _call_ase(self, func):
        '''Make a call to an ASE function.
        
        Handles changing directories
        
        Returns: Result of ASE function
        '''
        # Change directories
        old_path = os.getcwd()
        os.chdir(self._directory)
        
        # Call function
        try:
            res = func()
        except:
            os.chdir(old_path)
            raise
        
        # Change back
        os.chdir(old_path)
        return res
        
    def get_name(self):
    	'''Get the name of this program'''
        raise NotImplementedError
        
    def get_version_number(self):
        '''Get the version number of code that
        created these output files
        
        Returns:
            string, Version number
        '''
        raise NotImplementedError
    
    def get_output_structure(self):
        '''Get the output structure, if available
        
        Returns:
            ase.Atoms - Output structure from this calculation
                or None if output file not found
        '''
        raise NotImplementedError
    
    def get_composition(self):
        '''Get composition of output structure
        
        Returns:
            String - Composition based on output structure
        '''
        strc = self.get_output_structure()
        counts = Counter(strc.get_chemical_symbols())
        return ''.join(k if counts[k]==1 else '%s%d'%(k,counts[k]) \
                for k in sorted(counts))
        
    def get_cutoff_energy(self):
        '''Read the cutoff energy from the output
        
        Returns:
            tuple (float, string) - Cutoff energy and units
        '''
        
        raise NotImplementedError
    
    def uses_SOC(self):
        '''Parse the output file to tell if spin-orbit coupling was used
        
        Returns:
            bool
        '''
        
        raise NotImplementedError
        
    def is_relaxed(self):
        '''Parse the output file to tell if the structure was relaxed
        
        Returns:
            bool
        '''
        
        raise NotImplementedError
    
    def get_xc_functional(self):
        '''Parse the output file to tell which exchange-correlation functional was used
        
        Returns:
            string
        '''
        
        raise NotImplementedError

    def is_converged(self):
        '''Whether the calculation has converged
        
        Returns: boolean
        '''
        
        if not self._converged is None:
            return self._converged
        else:
            res = self._is_converged()
            self._converged = res
            return res
     

    def get_pp_name(self):
        '''Read output to get the pseudopotentials names used for each elements
        
        Returns:
            list - pseudopotentials names
        '''
        
        raise NotImplementedError


    def get_KPPRA(self):
        '''Read output and calculate the number of k-points per reciprocal atom
        
        Returns:
            tuple - (float - number of k-points per reciprocal atom, None)
        '''
        
        raise NotImplementedError

    def get_U_settings(self):
        '''Get the DFT+U settings, if used

        Returns: dict, which could contain several keys
            'DFT+U Type' -> String, type of DFT+U employed
            'DFT+U Values -> dict of Element -> (L, U, J)
        Note: Returns None if DFT+U was not used
        '''

        raise NotImplementedError

    def get_vdW_settings(self):
        '''Get the vdW settings, if applicable

        Returns: string, Type of vdW method employed'''

        raise NotImplementedError


    # Operations for retriving results
    def _is_converged(self):
        '''Read output to see whether it is converged
        
        Hidden operation: self.is_converged() is the public
        interface, which may draw from a converged result
        
        Returns: boolean'''
        
        raise NotImplementedError
        
    def get_total_energy(self):
        '''Get the total energy of the last ionic step
        
        Returns:
            tuple (float, string) - Total energy and units
        '''
        
        raise NotImplementedError
        
    def get_band_gap(self):
        '''Get the band gap energy

        Returns: tuple (float, string) - Band gap energy and units'''

        raise NotImplementedError

    def get_pressure(self):
        '''Get the pressure acting on the system

        Returns: type (float, string) - Pressure value and units'''

        raise NotImplementedError

    def get_dos(self):
        '''Get the total density of states

        Returns: dict, with the following keys
            energy_units -> string, units of energy
            energy -> list, energies at which DOS was evalauted
            dos_units -> string, units of DOS
            dos -> list, total DOS'''
            
        raise NotImplementedError

    def get_stresses(self):
       '''Get the stress tensor

       Returns: tuple (2d matrix, string) - Stress tensor and units'''

       raise NotImplementedError
