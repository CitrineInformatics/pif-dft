from pypif.obj import *
from .base import DFTParser, Value_if_true
import os
from dftparse.util import *
from dftparse.wien2k.scf_parser import ScfParser
from dftparse.wien2k.scf2_parser import Scf2Parser
from dftparse.wien2k.absorp_parser import AbsorpParser


class Wien2kParser(DFTParser):
    """
    Parser for Wien2k calculations
    """

    def get_name(self): return "Wien2k"
    
    def test_if_from(self, directory):
        # Check whether it has a .scf file (analogous to an OUTCAR file)
        for filename in os.listdir(directory):
            if os.path.splitext(filename)[1] == ".scf":
                return True
        return False

    def get_version_number(self):
        # Get version number from the .scf file
        for filename in os.listdir(self._directory):
            if os.path.splitext(filename)[1] == ".scf":

                with open(os.path.join(self._directory, filename)) as fp:

                    # look for line with ":LABEL3:"
                    for line in fp:
                        if ":LABEL3:" in line:
                            words = line.split()
                            return words[2].strip("WIEN2k_")

                # Error handling: version not found
                raise Exception("Wien2k version not found")

    def get_total_energy(self):
        # Get data the .scf file
        for filename in os.listdir(self._directory):
            if os.path.splitext(filename)[1] == ".scf":
                file_path = os.path.join(self._directory, filename)
        if not file_path:
            return None

        parser = ScfParser()
        with open(file_path, "r") as fp:
            matches = list(filter(lambda x: "total energy" in x, parser.parse(fp.readlines())))
        if len(matches) == 0:
            return None
        total_energy = matches[-1]["total energy"]
        total_energy_units = matches[-1]["total energy units"]
        return Property(scalars=[Scalar(value=total_energy)], units=total_energy_units)

    def get_band_gap(self):
        # Get data the .scf2 file
        for filename in os.listdir(self._directory):
            if os.path.splitext(filename)[1] == ".scf2":
                file_path = os.path.join(self._directory, filename)
        if not file_path:
            return None

        parser = Scf2Parser()
        with open(file_path, "r") as fp:
            matches = list(filter(lambda x: "band gap" in x, parser.parse(fp.readlines())))
        if len(matches) == 0:
            return None
        band_gap = matches[-1]["band gap"]
        band_gap_units = matches[-1]["band gap units"]
        return Property(scalars=[Scalar(value=band_gap)], units=band_gap_units)

    @staticmethod
    def _get_wavelengths(energy_lst):
        wavelgths_lst = []
        for energy in energy_lst:
            wavelgths_lst.append(Scalar(value=energy/1240))

        return wavelgths_lst

    @staticmethod
    def _get_scalars_lst(floats_lst):
        scalar_objs_lst = []
        for num in floats_lst:
            scalar_objs_lst.append(Scalar(value=num))

        return scalar_objs_lst

    @staticmethod
    def _extract_absorp_data(directory):
        # Get data from the .absorp file
        for filename in os.listdir(directory):
            if os.path.splitext(filename)[1] == ".absorp":
                file_path = os.path.join(directory, filename)
        if not file_path:
            return None

        parser = AbsorpParser()
        with open(file_path, "r") as fp:
            matches = list(filter(lambda x: "energy" in x, parser.parse(fp.readlines())))
        if len(matches) == 0:
            return None

        # Convert list of dics returned by dftparse to dic of lists
        non_empty_matches = remove_empty(matches)
        dic_of_lsts = transpose_list(non_empty_matches)

        return dic_of_lsts

    def get_optical_conductivity_xx(self):

        absorpdata_dic = Wien2kParser._extract_absorp_data(self._directory)

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(absorpdata_dic["energy"])
        re_sigma_xx = Wien2kParser._get_scalars_lst(absorpdata_dic["re_sigma_xx"])

        return Property(scalars=re_sigma_xx, units="1/(Ohm.cm)",
                        conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_optical_conductivity_zz(self):

        absorpdata_dic = Wien2kParser._extract_absorp_data(self._directory)

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(absorpdata_dic["energy"])
        re_sigma_xx = Wien2kParser._get_scalars_lst(absorpdata_dic["re_sigma_zz"])

        return Property(scalars=re_sigma_xx, units="1/(Ohm.cm)",
                        conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_absorp_xx(self):

        absorpdata_dic = Wien2kParser._extract_absorp_data(self._directory)

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(absorpdata_dic["energy"])
        re_sigma_xx = Wien2kParser._get_scalars_lst(absorpdata_dic["absorp_xx"])

        return Property(scalars=re_sigma_xx, units="10$^{4}$/cm",
                        conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_absorp_zz(self):

        absorpdata_dic = Wien2kParser._extract_absorp_data(self._directory)

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(absorpdata_dic["energy"])
        re_sigma_xx = Wien2kParser._get_scalars_lst(absorpdata_dic["absorp_zz"])

        return Property(scalars=re_sigma_xx, units="10$^{4}$/cm",
                        conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def uses_SOC(self):
        return None

    def is_relaxed(self):
        return None

    def get_U_settings(self):
        return None

    def get_vdW_settings(self):
        return None

    def get_pressure(self):
        return None

    def get_stresses(self):
        return None

    def get_dos(self):
        return None
