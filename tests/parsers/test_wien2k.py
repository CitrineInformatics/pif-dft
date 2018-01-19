import unittest
from dfttopif.parsers.wien2k import Wien2kParser
from ..test_pif import unpack_example, delete_example
import os
from pypif.obj import *


class TestWien2kParser(unittest.TestCase):

    def get_parser(self, name):
        """
        Get the Wien2kParser for a certain test
        """
        unpack_example(os.path.join("examples", "wien2k", name + ".tar.gz"))
        return Wien2kParser(name)

    def test_SiO2_opt(self):
        # Parse the results
        parser = self.get_parser(name="SiO2opt")

        # Test the settings
        self.assertEquals("Wien2k", parser.get_name())

        # Test that no composition is returned
        self.assertEquals(None, parser.get_composition())

        # total energy
        prop_energy = parser.get_total_energy()
        self.assertEquals(-780.127232, prop_energy.scalars[0].value)
        self.assertEquals("Ry", prop_energy.units)

        self.assertEquals(None, parser.uses_SOC())
        self.assertEquals(None, parser.is_relaxed())
        self.assertEquals("16.1", parser.get_version_number())
        self.assertEquals(None, parser.get_U_settings())
        self.assertEquals(None, parser.get_vdW_settings())
        self.assertEquals(None, parser.get_pressure())
        self.assertEquals(None, parser.get_stresses())
        self.assertEquals(None, parser.get_dos())

        # band gap
        prop_bandgap = parser.get_band_gap()
        self.assertEquals(0.709, prop_bandgap.scalars[0].value)
        self.assertEquals("eV", prop_bandgap.units)

        # .absorp
        absorp_prop = parser.get_absorp()
        self.assertIsInstance(absorp_prop, Property)
        self.assertEquals(len(absorp_prop.scalars), 8)
        self.assertAlmostEqual(round(absorp_prop.scalars[0].value, 8), 0.13105967)
        self.assertEquals(absorp_prop.units, "10$^{4}$/cm")

        cond_notfound = True
        for cond in absorp_prop.conditions:
            if cond.name == "Wavelength":
                cond_notfound = False
                self.assertEquals(cond.units, "/nm")
                self.assertEquals(len(cond.scalars), 8)
                self.assertAlmostEqual(cond.scalars[0].value, 0.00044986)

        if cond_notfound:
            raise ValueError("Condition 'Wavelength' not found")

        # .eloss
        eloss_prop = parser.get_eloss()
        self.assertIsInstance(eloss_prop, Property)
        self.assertEquals(len(eloss_prop.scalars), 6)
        self.assertEquals(round(eloss_prop.scalars[0].value, 3), 0.069)

        cond_notfound = True
        for cond in eloss_prop.conditions:
            if cond.name == "Wavelength":
                cond_notfound = False
                self.assertEquals(cond.units, "/nm")
                self.assertEquals(len(cond.scalars), 6)
                self.assertAlmostEqual(round(cond.scalars[0].value, 4), 0.0024)

        if cond_notfound:
            raise ValueError("Condition 'Wavelength' not found")

        # .epsilon
        im_eps_prop = parser.get_im_eps()
        self.assertIsInstance(im_eps_prop, Property)
        self.assertEquals(len(im_eps_prop.scalars), 6)
        self.assertEquals(round(im_eps_prop.scalars[0].value, 3), 0.137)

        cond_notfound = True
        for cond in im_eps_prop.conditions:
            if cond.name == "Frequency":
                cond_notfound = False
                self.assertEquals(cond.units, "/s")
                self.assertEquals(len(cond.scalars), 6)
                self.assertAlmostEqual(round(cond.scalars[0].value, 4), 128303916000000.0)

        if cond_notfound:
            raise ValueError("Condition 'Frequency' not found")

        # .reflectivity
        reflect_prop = parser.get_reflect()
        self.assertIsInstance(reflect_prop, Property)
        self.assertEquals(len(reflect_prop.scalars), 6)
        self.assertEquals(round(reflect_prop.scalars[0].value, 3), 0.259)

        cond_notfound = True
        for cond in reflect_prop.conditions:
            if cond.name == "Wavelength":
                cond_notfound = False
                self.assertEquals(cond.units, "/nm")
                self.assertEquals(len(cond.scalars), 6)
                self.assertAlmostEqual(round(cond.scalars[0].value, 6), 0.000757)

        if cond_notfound:
            raise ValueError("Condition 'Wavelength' not found")

        # .refraction
        ref_ind_prop = parser.get_ref_ind()
        self.assertIsInstance(ref_ind_prop, Property)
        self.assertEquals(len(ref_ind_prop.scalars), 6)
        self.assertEquals(round(ref_ind_prop.scalars[0].value, 4), 3.3195)

        cond_notfound = True
        for cond in ref_ind_prop.conditions:
            if cond.name == "Wavelength":
                cond_notfound = False
                self.assertEquals(cond.units, "/nm")
                self.assertEquals(len(cond.scalars), 6)
                self.assertAlmostEqual(round(cond.scalars[0].value, 5), 0.00126)

        if cond_notfound:
            raise ValueError("Condition 'Wavelength' not found")

        # Delete the data
        delete_example("SiO2opt")


if __name__ == '__main__':
    unittest.main()
