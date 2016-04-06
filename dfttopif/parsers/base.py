class DFTParser:
    """
    Base class for all tools to parse a directory
    of output files from a DFT Calculation
    """
    
    _directory = None
    """Path to directory containing calculation files"""
    
    def __init__(self, directory):
        """Intialize a parser. 
        
        Input:
            directory - String, path to a directory of output files
        """
        
        # Sanity check: Make sure the format is correct
        if not self.test_if_from(directory):
            raise Exception('Files in directory inconsistant with this format')
            
        self._directory = directory
      
    @classmethod
    def test_if_from(self, directory):
        """Test whether a directory of output files
        seems like it is from this DFT code.
        
        Input:
            directory - String, path to a directory of output files
        Returns: 
            boolean, whether directory was created by this code
        """
        
        raise NotImplementedError
        
    def get_name(self):
    	"""Get the name of this program"""
        raise NotImplementedError
        
    def get_version_number(self):
        """Get the version number of code that
        created these output files
        
        Returns:
            string, Version number
        """
        
        raise NotImplementedError
        
    def get_cutoff_energy(self):
        """Read the cutoff energy from the output
        
        Returns:
            tuple (float, string) - Cutoff energy and units
        """
        
        raise NotImplementedError
        
