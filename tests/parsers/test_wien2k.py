import unittest
from dfttopif.parsers.wien2k import Wien2kParser
from ..test_pif import unpack_example, delete_example
import os


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

        prop_bandgap = parser.get_band_gap()
        self.assertEquals(0.709, prop_bandgap.scalars[0].value)
        self.assertEquals("eV", prop_bandgap.units)

        absorp_props = parser.get_absorption()

        self.assertEquals(len(absorp_props), 4)

        for absorp_prop in absorp_props:
            if absorp_prop.name == "Re $\sigma_{xx}$":
                self.assertEquals(len(absorp_prop.scalars), 8)
                self.assertEquals(absorp_prop.scalars[0].value, 11.508)
                self.assertEquals(absorp_prop.units, "1/(Ohm.cm)")

                cond_notfound = True
                for cond in absorp_prop.conditions:
                    if cond.name == "Wavelength":
                        cond_notfound = False
                        self.assertEquals(cond.units, "nm")
                        self.assertEquals(len(cond.scalars), 8)
                        self.assertAlmostEqual(cond.scalars[0].value, 0.00044986)

                if cond_notfound:
                    raise ValueError("Condition 'Wavelength' not found")

            elif absorp_prop.name == "$\\alpha_{zz}$":
                self.assertEquals(len(absorp_prop.scalars), 8)
                self.assertEquals(absorp_prop.scalars[7].value, 194.137)
                self.assertEquals(absorp_prop.units, "10$^{4}$/cm")

                cond_notfound = True
                for cond in absorp_prop.conditions:
                    if cond.name == "Wavelength":
                        cond_notfound = False
                        self.assertEquals(cond.units, "nm")
                        self.assertEquals(len(cond.scalars), 8)
                        self.assertAlmostEqual(round(cond.scalars[7].value, 6), 0.010566)

                if cond_notfound:
                    raise ValueError("Condition 'Wavelength' not found")

        # Delete the data
        delete_example("SiO2opt")


if __name__ == '__main__':
    unittest.main()
