import unittest
from dfttopif import directory_to_pif
import tarfile
import os
import shutil
from pypif import pif
import glob

def delete_example(name):
    '''Delete example files that were unpacked
    using the `unpack_example(path)` function
    
    Input:
        name - Name of example file
    '''
    shutil.rmtree(name)

def unpack_example(path):
    '''Unpack a VASP test case to a temporary directory
    
    Input:
        path - String, path to tar.gz file containing
            a certain test case
    '''
    
    # Open the tar file
    tp = tarfile.open(path)
    
    # Extract to cwd
    tp.extractall()


class TestPifGenerator(unittest.TestCase):
    '''
    Tests for the tool that generates the pif objects
    '''
    
    def test_VASP(self):
        '''
        Test ability to parse VASP directories
        '''
        
        for file in glob.glob(os.path.join('examples','vasp','*.tar.gz')):
            # Get the example files
            unpack_example(file)
            name = ".".join(os.path.basename(file).split(".")[:-2])
            
            # Make the pif file
            print "\tpif for example:", name
            result = directory_to_pif(name)
            print pif.dumps(result, indent=4)
            
            # Delete files
            delete_example(name)
        
if __name__ == '__main__':
    unittest.main()