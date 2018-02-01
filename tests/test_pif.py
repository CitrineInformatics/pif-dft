import unittest
from dfttopif import directory_to_pif, convert
import tarfile
import os
import shutil
import glob

def delete_example(name):
    '''Delete example files that were unpacked
    using the `unpack_example(path)` function
    
    Input:
        name - Name of example file
    '''
    shutil.rmtree(name)

def unpack_example(path):
    '''Unpack a test case to a temporary directory
    
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
        
        test_quality_report = True
        for file in glob.glob(os.path.join('examples','vasp','*.tar.gz')):
            # Get the example files
            unpack_example(file)
            name = ".".join(os.path.basename(file).split(".")[:-2])
            
            # Make the pif file
            # print("\tpif for example:", name)
            result = directory_to_pif(name, quality_report=test_quality_report)
            # Only hit the quality report endpoint once to avoid load spikes in automated tests
            test_quality_report=False
            assert result.chemical_formula is not None
            assert result.properties is not None
            # print(pif.dumps(result, indent=4))
            
            # Delete files
            delete_example(name)

        # Test if we only have a single OUTCAR
        unpack_example(os.path.join('examples', 'vasp', 'AlNi_static_LDA.tar.gz'))

        #  Remove all files but OUTCAR
        for f in os.listdir('AlNi_static_LDA'):
            if f != 'OUTCAR':
                os.unlink(os.path.join('AlNi_static_LDA', f))

        convert([os.path.join('AlNi_static_LDA', 'OUTCAR')], quality_report=False)

        delete_example('AlNi_static_LDA')

    def test_PWSCF(self):
        '''
        Test ability to parse PWSCF directories
        '''
        
        for file in glob.glob(os.path.join('examples','pwscf','*.tar.gz')):
            # Get the example files
            unpack_example(file)
            name = ".".join(os.path.basename(file).split(".")[:-2])
            
            # Make the pif file
            # print("\tpif for example:", name)
            result = directory_to_pif(name)
            assert result.chemical_formula is not None
            assert result.properties is not None
            # print(pif.dumps(result, indent=4))
            
            # Delete files
            delete_example(name)
        
if __name__ == '__main__':
    unittest.main()
