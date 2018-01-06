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
        re_sigma_xx_prop = parser.get_optical_conductivity_xx()
        self.assertIsInstance(re_sigma_xx_prop, Property)
        self.assertEquals(len(re_sigma_xx_prop.scalars), 8)
        self.assertEquals(re_sigma_xx_prop.scalars[0].value, 11.508)
        self.assertEquals(re_sigma_xx_prop.units, "1/(Ohm.cm)")

        cond_notfound = True
        for cond in re_sigma_xx_prop.conditions:
            if cond.name == "Wavelength":
                cond_notfound = False
                self.assertEquals(cond.units, "nm")
                self.assertEquals(len(cond.scalars), 8)
                self.assertAlmostEqual(cond.scalars[0].value, 0.00044986)

        if cond_notfound:
            raise ValueError("Condition 'Wavelength' not found")

        absorp_zz_prop = parser.get_absorp_zz()
        self.assertIsInstance(absorp_zz_prop, Property)
        self.assertEquals(len(absorp_zz_prop.scalars), 8)
        self.assertEquals(absorp_zz_prop.scalars[7].value, 194.137)
        self.assertEquals(absorp_zz_prop.units, "10$^{4}$/cm")

        # .eloss
        eloss_xx_prop = parser.get_eloss_xx()
        self.assertIsInstance(eloss_xx_prop, Property)
        self.assertEquals(len(eloss_xx_prop.scalars), 6)
        self.assertEquals(eloss_xx_prop.scalars[0].value, 0.0672767)

        cond_notfound = True
        for cond in eloss_xx_prop.conditions:
            if cond.name == "Wavelength":
                cond_notfound = False
                self.assertEquals(cond.units, "nm")
                self.assertEquals(len(cond.scalars), 6)
                self.assertAlmostEqual(round(cond.scalars[0].value, 4), 0.0024)

        if cond_notfound:
            raise ValueError("Condition 'Wavelength' not found")

        # .epsilon
        im_eps_xx_prop = parser.get_im_eps_xx()
        self.assertIsInstance(im_eps_xx_prop, Property)
        self.assertEquals(len(im_eps_xx_prop.scalars), 6)
        self.assertEquals(im_eps_xx_prop.scalars[0].value, 0.149891)

        cond_notfound = True
        for cond in im_eps_xx_prop.conditions:
            if cond.name == "Frequency":
                cond_notfound = False
                self.assertEquals(cond.units, "Hz")
                self.assertEquals(len(cond.scalars), 6)
                self.assertAlmostEqual(round(cond.scalars[0].value, 4), 128303916000000.0)

        if cond_notfound:
            raise ValueError("Condition 'Frequency' not found")

        re_eps_zz_prop = parser.get_re_eps_zz()
        self.assertIsInstance(re_eps_zz_prop, Property)
        self.assertEquals(len(re_eps_zz_prop.scalars), 6)
        self.assertEquals(re_eps_zz_prop.scalars[0].value, 8.01805)

        # .reflectivity
        reflect_xx_prop = parser.get_reflect_xx()
        self.assertIsInstance(reflect_xx_prop, Property)
        self.assertEquals(len(reflect_xx_prop.scalars), 6)
        self.assertEquals(reflect_xx_prop.scalars[0].value, 0.270998)

        cond_notfound = True
        for cond in reflect_xx_prop.conditions:
            if cond.name == "Wavelength":
                cond_notfound = False
                self.assertEquals(cond.units, "nm")
                self.assertEquals(len(cond.scalars), 6)
                self.assertAlmostEqual(round(cond.scalars[0].value, 6), 0.000757)

        if cond_notfound:
            raise ValueError("Condition 'Wavelength' not found")

        # Delete the data
        delete_example("SiO2opt")


if __name__ == '__main__':
    unittest.main()
