from pypif.obj import *
from .base import DFTParser
import os
from dftparse.util import *
from dftparse.wien2k.scf_parser import ScfParser
from dftparse.wien2k.scf2_parser import Scf2Parser
from dftparse.wien2k.sigmak_parser import SigmakParser
from dftparse.wien2k.absorp_parser import AbsorpParser
from dftparse.wien2k.eloss_parser import ElossParser
from dftparse.wien2k.epsilon_parser import EpsilonParser
from dftparse.wien2k.reflectivity_parser import ReflectivityParser
from dftparse.wien2k.refract_parser import RefractionParser
from ase.io.wien2k import read_struct


class Wien2kParser(DFTParser):
    """
    Parser for Wien2k calculations
    """

    def get_name(self): return "Wien2k"

    def get_result_functions(self):
        base_results = super(Wien2kParser, self).get_result_functions()
        base_results["Re Optical conductivity (Re $\sigma$)"] = "get_re_optical_conductivity"
        base_results["Im Optical conductivity (Im $\sigma$)"] = "get_im_optical_conductivity"
        base_results["Absorption ($\\alpha$)"] = "get_absorp"
        base_results["eloss"] = "get_eloss"
        base_results["Re $\\varepsilon$"] = "get_re_eps"
        base_results["Im $\\varepsilon$"] = "get_im_eps"
        base_results["reflect"] = "get_reflect"
        base_results["ref_ind"] = "get_ref_ind"
        base_results["extinct"] = "get_extinct"
        return base_results

    def test_if_from(self, directory):
        # Check whether it has a .scf file (analogous to an OUTCAR file)
        for filename in os.listdir(directory):
            if os.path.splitext(filename)[1] == ".scf" and filename[:2] != "._":
                with open(os.path.join(directory, filename)) as fp:
                    for line in fp:
                        if "using WIEN2k" in line or ":ITE001:  1. ITERATION" in line:
                            return True
        return False

    @staticmethod
    def _get_file(directory, ext):
        # Get appropriate file, that does not being with "._"
        for filename in os.listdir(directory):
            if os.path.splitext(filename)[1] == ext and filename[:2] != "._":
                return filename

    def get_version_number(self):
        # Get version number from the .scf file
        filename = Wien2kParser._get_file(self._directory, ".scf")
        with open(os.path.join(self._directory, filename)) as fp:
            # look for line with ":LABEL3:"
            for line in fp:
                if ":LABEL3:" in line:
                    words = line.split()
                    return words[2].strip("WIEN2k_")
        # Error handling: version not found
        raise ValueError("Wien2k version not found")

    def get_total_energy(self):
        # Get data the .scf file
        filename = Wien2kParser._get_file(self._directory, ".scf")
        file_path = os.path.join(self._directory, filename)
        if not file_path:
            return None

        parser = ScfParser()
        with open(file_path, "r") as fp:
            matches = [x for x in parser.parse(fp.readlines()) if "total energy" in x]
        if len(matches) == 0:
            return None
        total_energy = matches[-1]["total energy"]
        total_energy_units = matches[-1]["total energy units"]
        return Property(scalars=[Scalar(value=total_energy)], units=total_energy_units)

    def get_band_gap(self):
        # Get data the .scf2 file
        filename = Wien2kParser._get_file(self._directory, ".scf2")
        file_path = os.path.join(self._directory, filename)
        if not file_path:
            return None

        parser = Scf2Parser()
        with open(file_path, "r") as fp:
            matches = [x for x in parser.parse(fp.readlines()) if "band gap" in x]
        if len(matches) == 0:
            return None
        band_gap = matches[-1]["band gap"]
        band_gap_units = matches[-1]["band gap units"]
        return Property(scalars=[Scalar(value=band_gap)], units=band_gap_units)

    @staticmethod
    def _get_wavelengths(energy_lst):
        return [Scalar(value=1240.0/energy) for energy in energy_lst]

    @staticmethod
    def _get_frequencies(energy_lst):
        return [Scalar(value=energy*2.418*10**14) for energy in energy_lst]

    @staticmethod
    def _get_scalars_lst(floats_lst):
        return [Scalar(value=num) for num in floats_lst]

    @staticmethod
    def _extract_file_data(directory, ext):
        # Get data from the file
        filename = Wien2kParser._get_file(directory, ext)
        file_path = os.path.join(directory, filename)
        if not file_path:
            return None

        if ext == ".absorp":
            parser = AbsorpParser()
        elif ext == ".sigmak":
            parser = SigmakParser()
        elif ext == ".eloss":
            parser = ElossParser()
        elif ext == ".epsilon":
            parser = EpsilonParser()
        elif ext == ".reflectivity":
            parser = ReflectivityParser()
        elif ext == ".refraction":
            parser = RefractionParser()
        else:
            raise ValueError("Unrecognized extension: {}".format(ext))

        with open(file_path, "r") as fp:
            matches = [x for x in parser.parse(fp.readlines()) if "energy" in x]
        if len(matches) == 0:
            return None

        # Convert list of dics returned by dftparse to dic of lists
        non_empty_matches = remove_empty(matches)
        dic_of_lsts = transpose_list(non_empty_matches)

        return dic_of_lsts

    def get_re_optical_conductivity(self):

        sigmakdata_dic = Wien2kParser._extract_file_data(self._directory, ".sigmak")

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(sigmakdata_dic["energy"])
        re_sigma_xx = sigmakdata_dic["re_sigma_xx"]
        re_sigma_zz = sigmakdata_dic["re_sigma_zz"]

        re_sigma = Wien2kParser._get_scalars_lst([((2 * re_sigma_xx[i]) + re_sigma_zz[i])/3
                                                  for i in range(len(re_sigma_xx))])

        return Property(scalars=re_sigma, units="10$^{15}$/sec",
                        conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_im_optical_conductivity(self):

        sigmakdata_dic = Wien2kParser._extract_file_data(self._directory, ".sigmak")

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(sigmakdata_dic["energy"])
        im_sigma_xx = sigmakdata_dic["im_sigma_xx"]
        im_sigma_zz = sigmakdata_dic["im_sigma_zz"]

        im_sigma = Wien2kParser._get_scalars_lst([((2 * im_sigma_xx[i]) + im_sigma_zz[i])/3
                                                  for i in range(len(im_sigma_xx))])

        return Property(scalars=im_sigma, units="10$^{15}$/sec",
                        conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_absorp(self):

        absorpdata_dic = Wien2kParser._extract_file_data(self._directory, ".absorp")

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(absorpdata_dic["energy"])
        absorp_xx = absorpdata_dic["absorp_xx"]
        absorp_zz = absorpdata_dic["absorp_zz"]

        absorp = Wien2kParser._get_scalars_lst([((2 * absorp_xx[i]) + absorp_zz[i])/3 for i in range(len(absorp_xx))])

        return Property(scalars=absorp, units="10$^{4}$/cm",
                        conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_eloss(self):

        elossdata_dic = Wien2kParser._extract_file_data(self._directory, ".eloss")

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(elossdata_dic["energy"])
        eloss_xx = elossdata_dic["eloss_xx"]
        eloss_zz = elossdata_dic["eloss_zz"]

        eloss = Wien2kParser._get_scalars_lst([((2 * eloss_xx[i]) + eloss_zz[i])/3 for i in range(len(eloss_xx))])

        return Property(scalars=eloss, conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_re_eps(self):

        epsdata_dic = Wien2kParser._extract_file_data(self._directory, ".epsilon")

        # Get frequency and other scalar lists
        frequencies = Wien2kParser._get_frequencies(epsdata_dic["energy"])
        re_eps_xx = epsdata_dic["re_eps_xx"]
        re_eps_zz = epsdata_dic["re_eps_zz"]

        re_eps = Wien2kParser._get_scalars_lst([((2 * re_eps_xx[i]) + re_eps_zz[i])/3 for i in range(len(re_eps_xx))])

        return Property(scalars=re_eps, conditions=[Value(name="Frequency", units="/s", scalars=frequencies)])

    def get_im_eps(self):

        epsdata_dic = Wien2kParser._extract_file_data(self._directory, ".epsilon")

        # Get frequency and other scalar lists
        frequencies = Wien2kParser._get_frequencies(epsdata_dic["energy"])
        im_eps_xx = epsdata_dic["im_eps_xx"]
        im_eps_zz = epsdata_dic["im_eps_zz"]

        im_eps = Wien2kParser._get_scalars_lst([((2 * im_eps_xx[i]) + im_eps_zz[i])/3 for i in range(len(im_eps_xx))])

        return Property(scalars=im_eps, conditions=[Value(name="Frequency", units="/s", scalars=frequencies)])

    def get_reflect(self):

        reflectdata_dic = Wien2kParser._extract_file_data(self._directory, ".reflectivity")

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(reflectdata_dic["energy"])
        reflect_xx = reflectdata_dic["reflect_xx"]
        reflect_zz = reflectdata_dic["reflect_zz"]

        reflect = Wien2kParser._get_scalars_lst([((2 * reflect_xx[i]) + reflect_zz[i])/3
                                                 for i in range(len(reflect_xx))])

        return Property(scalars=reflect, conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_ref_ind(self):

        refractdata_dic = Wien2kParser._extract_file_data(self._directory, ".refraction")

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(refractdata_dic["energy"])
        ref_ind_xx = refractdata_dic["ref_ind_xx"]
        ref_ind_zz = refractdata_dic["ref_ind_zz"]

        ref_ind = Wien2kParser._get_scalars_lst([((2 * ref_ind_xx[i]) + ref_ind_zz[i])/3
                                                 for i in range(len(ref_ind_xx))])

        return Property(scalars=ref_ind, conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_extinct(self):

        refractdata_dic = Wien2kParser._extract_file_data(self._directory, ".refraction")

        # Get wavelengths and other scalar lists
        wavelengths = Wien2kParser._get_wavelengths(refractdata_dic["energy"])
        extinct_xx = refractdata_dic["extinct_xx"]
        extinct_zz = refractdata_dic["extinct_zz"]

        extinct = Wien2kParser._get_scalars_lst([((2 * extinct_xx[i]) + extinct_zz[i])/3
                                                 for i in range(len(extinct_xx))])

        return Property(scalars=extinct, conditions=[Value(name="Wavelength", units="nm", scalars=wavelengths)])

    def get_composition(self):
        file_path = None
        filename = Wien2kParser._get_file(self._directory, ".struct")
        file_path = os.path.join(self._directory, filename)

        atom_obj = read_struct(file_path)
        return atom_obj.get_chemical_formula()

    def get_xc_functional(self):
        return None

    def is_relaxed(self):
        return None

    def get_cutoff_energy(self):
        return None

    def get_KPPRA(self):
        return None

    def uses_SOC(self):
        return None

    def get_U_settings(self):
        return None

    def get_vdW_settings(self):
        return None

    def get_pp_name(self):
        return None

    def get_incar(self):
        return None

    def get_poscar(self):
        return None

    def is_converged(self):
        return None

    def get_pressure(self):
        return None

    def get_dos(self):
        return None

    def get_positions(self):
        return None

    def get_forces(self):
        return None

    def get_total_force(self):
        return None

    def get_density(self):
        return None

    def get_outcar(self):
        return None

    def get_total_magnetization(self):
        return None

    def get_stresses(self):
        return None


