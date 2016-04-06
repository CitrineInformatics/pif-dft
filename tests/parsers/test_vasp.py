import unittest
from dfttopif.parsers import VaspParser
import tarfile
import os
import shutil

class TestVASPParser(unittest.TestCase):

    def unpack_example(self,path):
        """Unpack a VASP test case to a temporary directory
        
        Input:
            path - String, path to tar.gz file containing
                a certain test case
        """
        
        # Open the tar file
        tp = tarfile.open(path)
        
        # Extract to cwd
        tp.extractall()
        
    def get_parser(self,name):
        """Get a VaspParser for a certain test"""
        self.unpack_example(os.path.join('examples','vasp',name+'.tar.gz'))
        return VaspParser(name)
    
    def delete_example(self, name):
        shutil.rmtree(name)

    def test_perov(self):
        # Parse the results
        parser = self.get_parser('perov_relax_U')
        
        # Test the settings
        self.assertEquals('VASP', parser.get_name())
        self.assertEquals((400,'eV'), parser.get_cutoff_energy())
        self.assertEquals(True, parser.is_converged())
        self.assertAlmostEqual(-39.85550532, parser.get_total_energy()[0])
        self.assertEquals('eV', parser.get_total_energy()[1])
        self.assertEquals(False, parser.uses_SOC())        
        self.assertEquals(True, parser.is_relaxed())    
        self.assertEquals('PAW_PBE', parser.get_xc_functional())
        self.assertEquals(['La','Mn','O'], parser.get_pp_name())        
        self.assertEquals(8640, parser.get_KPPRA())
        self.assertEquals('5.3.2', parser.get_version_number())
        
        # Delete the data
        self.delete_example('perov_relax_U')
        
    def test_AlNi(self):
        # Parse the results
        parser = self.get_parser('AlNi_static_LDA')
        
        # Test the settings
        self.assertEquals('VASP', parser.get_name())
        self.assertEquals((650,'eV'), parser.get_cutoff_energy())
        self.assertEquals(True, parser.is_converged())
        self.assertAlmostEqual(-12.19669689, parser.get_total_energy()[0])
        self.assertEquals('eV', parser.get_total_energy()[1])
        self.assertEquals(False, parser.uses_SOC())
        self.assertEquals(False, parser.is_relaxed())
        self.assertEquals('PAW', parser.get_xc_functional())
        self.assertEquals(['Al','Ni'], parser.get_pp_name())   
        self.assertEquals(8192, parser.get_KPPRA())
        self.assertEquals('5.3.2', parser.get_version_number())
        
        # Delete the data
        self.delete_example('AlNi_static_LDA')
        
    def test_SOC(self):
        # Parse the results
        parser = self.get_parser('heusler_static_SOC')
        
        # Test the settings
        self.assertEquals('VASP', parser.get_name())
        self.assertEquals((499,'eV'), parser.get_cutoff_energy())
        self.assertEquals(True, parser.is_converged())
        self.assertAlmostEqual(-22.273992, parser.get_total_energy()[0])
        self.assertEquals('eV', parser.get_total_energy()[1])
        self.assertEquals(True, parser.uses_SOC())
        self.assertEquals(False, parser.is_relaxed())
        self.assertEquals('PAW_PBE', parser.get_xc_functional())
        self.assertEquals(['Li_sv','Pt','Sn_d','Y_sv'], parser.get_pp_name()) 
        self.assertEquals(1440, parser.get_KPPRA())
        self.assertEquals('5.2.11', parser.get_version_number())
        
        # Delete the data
        self.delete_example('heusler_static_SOC')
        
    def test_vdW(self):
        # Parse the results
        parser = self.get_parser('vdW')
        
        # Test the settings
        self.assertEquals('VASP', parser.get_name())
        self.assertEquals((520,'eV'), parser.get_cutoff_energy())
        self.assertEquals(True, parser.is_converged())
        self.assertAlmostEqual(-707.48169596, parser.get_total_energy()[0])
        self.assertEquals('eV', parser.get_total_energy()[1])
        self.assertEquals(False, parser.uses_SOC())
        self.assertEquals(True, parser.is_relaxed())
        self.assertEquals('PAW_PBE', parser.get_xc_functional())
        self.assertEquals(['C','H','Br','Fe','N','S'], parser.get_pp_name())
        self.assertEquals(142, parser.get_KPPRA())    
        self.assertEquals('5.3.5', parser.get_version_number())
        
        # Delete the data
        self.delete_example('vdW')
        
if __name__ == '__main__':
    unittest.main()
