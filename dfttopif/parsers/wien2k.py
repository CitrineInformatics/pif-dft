from pypif.obj import *
from .base import DFTParser, Value_if_true
import os
from dftparse.wien2k.scf_parser import ScfParser


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
        # Open up the .scf file
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
        # Get the .scf file
        for filename in os.listdir(self._directory):
            if os.path.splitext(filename)[1] == ".scf":
                file_path = os.path.join(self._directory, filename)
        if not file_path:
            return None

        parser = ScfParser()
        with open(file_path, "r") as fp:
            matches = list(filter(lambda x: ":ENE" in x, parser.parse(fp.readlines())))
        if len(matches) == 0:
            return None
        total_energy = matches[-1]["total energy"]
        total_energy_units = matches[-1]["total energy units"]
        return Property(scalars=[Scalar(value=total_energy)], units=total_energy_units)
