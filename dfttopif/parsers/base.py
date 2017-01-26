import os
from collections import Counter
from pypif.obj.common import Value, Property


def Value_if_true(func):
    '''Returns:
        Value if x is True, else None'''
    return lambda x: Value() if func(x) == True else None


class DFTParser(object):
    '''Base class for all tools to parse a directory of output files from a DFT Calculation
    
    To use this class, provide the path to a directory to containing the output files from a DFT calculation. Once
     instantiated, call the methods provided by this class in order to retrieve the settings and results of the
     calculation.
    
    To get a list of names of the settings available for this a particular instance, call get_setting_functions(). These
     methods return a pypif Value object.
    
    To get a list of the names of results available via a particular instance, call get_result_functions(). These
     methods return a pypif Property object.

    Developer Notes
    ---------------
    
    Settings and properties should...
        return None if property or setting is not applicable, or if the test is a boolean and the value is false
        Raise exception if there is an error that would benefit from user intervention

    To add a new setting or value to the output, add a new entry to the dictionary returned by get_setting_functions()
     or get_result_functions(). The key for each entry is a 'human-friendly' name of the result and the value is the
     name of the function. This design was chosen because there is a single function for defining the human names of the
     results, which are what serve as the tags in the pif file. In this way, the same property will be ensured to
     have the same name in the pif.
    '''
    
    _directory = None
    '''Path to directory containing calculation files'''
    
    _converged = None
    ''' Whether this calculation has converged '''
    
    def __init__(self, directory):
        '''Initialize a parser.
        
        Input:
            directory - String, path to a directory of output files
        '''
        
        # Sanity check: Make sure the format is correct
        if not self.test_if_from(directory):
            raise Exception('Files in directory inconsistent with this format')
            
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
                and the value is function name of this parser
        '''
        return {
            'XC Functional':'get_xc_functional',
            'Relaxed':'is_relaxed',
            'Cutoff Energy':'get_cutoff_energy',
            'k-Points per Reciprocal Atom':'get_KPPRA',
            'Spin-Orbit Coupling':'uses_SOC',
            'DFT+U':'get_U_settings',
            'vdW Interactions':'get_vdW_settings',
            'Psuedopotentials':'get_pp_name',
            'INCAR':'get_incar',
            'POSCAR':'get_poscar',
        }
        
    def get_result_functions(self):
        '''Get a dictionary describing the names of methods 
        that return results of the calculation
        
        Returns:
            dict, where the key is the name of a property,
                and the value is the name of the function
        '''
        return {
            'Converged':'is_converged',
            'Total Energy':'get_total_energy',
            'Band Gap Energy':'get_band_gap',
            'Pressure':'get_pressure',
            'Density of States':'get_dos',
            'Positions': 'get_positions',
            'Forces': 'get_forces',
            'OUTCAR': 'get_outcar',
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

    def get_positions(self):
        strc = self.get_output_structure()
        return Property(vectors=strc.positions.tolist())

    def get_cutoff_energy(self):
        '''Read the cutoff energy from the output
        
        Returns:
            Value, cutoff energy (scalar) and units
        '''
        
        raise NotImplementedError
    
    def uses_SOC(self):
        '''Parse the output file to tell if spin-orbit coupling was used
        
        Returns:
            Blank Value if true, `None` otherwise
        '''
        
        raise NotImplementedError
        
    def is_relaxed(self):
        '''Parse the output file to tell if the structure was relaxed
        
        Returns:
            Blank Value if true, `None` otherwise
        '''
        
        raise NotImplementedError
    
    def get_xc_functional(self):
        '''Parse the output file to tell which exchange-correlation functional was used
        
        Returns:
            Value - where "scalars" is the name of the functional
        '''
        
        raise NotImplementedError

    def is_converged(self):
        '''Whether the calculation has converged
        
        Returns: Property where "scalar" is a boolean indicating
        '''

        # Check for cached result
        if self._converged is None:
            self._converged = self._is_converged()
        return Property(scalars=self._converged)

    def get_pp_name(self):
        '''Read output to get the pseudopotentials names used for each elements
        
        Returns:
            Value where the key "scalars" is the list of pseudopotentials names
        '''
        
        raise NotImplementedError

    def get_KPPRA(self):
        '''Read output and calculate the number of k-points per reciprocal atom
        
        Returns:
            Value, number of k-points per reciprocal atom
        '''
        
        raise NotImplementedError

    def get_U_settings(self):
        '''Get the DFT+U settings, if used

        Returns: Value, which could contain several keys
            'Type' -> String, type of DFT+U employed
            'Values' -> dict of Element -> (L, U, J)
        Note: Returns None if DFT+U was not used
        '''

        raise NotImplementedError

    def get_vdW_settings(self):
        '''Get the vdW settings, if applicable

        Returns: Value where `scalars` is the name of the vdW method. None if vdW was not used'''

        raise NotImplementedError

    # Operations for retrieving results
    def _is_converged(self):
        '''Read output to see whether it is converged
        
        Hidden operation: self.is_converged() is the public
        interface, which may draw from a converged result
        
        Returns: boolean'''
        
        raise NotImplementedError
        
    def get_total_energy(self):
        '''Get the total energy of the last ionic step
        
        Returns: Property
        '''
        
        raise NotImplementedError
        
    def get_band_gap(self):
        '''Get the band gap energy

        Returns: Property'''

        raise NotImplementedError

    def get_pressure(self):
        '''Get the pressure acting on the system

        Returns: Property, where pressure is a scalar'''

        raise NotImplementedError

    def get_dos(self):
        '''Get the total density of states

        Returns: Property where DOS is a vector, and the energy at which the DOS was evaluated is a condition'''
            
        raise NotImplementedError

    def get_stresses(self):
       '''Get the stress tensor

       Returns: Property where stresses is a 2d matrix'''

       raise NotImplementedError
