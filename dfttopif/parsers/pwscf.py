from pypif.obj.common import Property, Scalar

from .base import DFTParser, Value_if_true, InvalidIngesterException
import os
from pypif.obj.common.value import Value
from dftparse.pwscf.stdout_parser import PwscfStdOutputParser
from ase import Atoms


class PwscfParser(DFTParser):
    '''
    Parser for PWSCF calculations
    '''

    def __init__(self, files):
        super(PwscfParser, self).__init__(files)
        self.settings = {}
        parser = PwscfStdOutputParser()

        # Look for appropriate files
        self.inputf = self.outputf = None
        for f in self._files:
            try:
                if self._get_line('Program PWSCF', f, return_string=False):
                    if self.outputf is not None:
                        raise InvalidIngesterException('More than one output file!')
                    self.outputf = f
                elif self._get_line('&control', f, return_string=False, case_sens=False):
                    if self.inputf is not None:
                        raise InvalidIngesterException('More than one input file')
                    self.inputf = f
            except UnicodeDecodeError as e:
                pass

        if self.inputf is None:
            raise InvalidIngesterException('Failed to find input file')
        if self.outputf is None:
            raise InvalidIngesterException('Failed to find output file')

        # Read in the settings
        with open(self.outputf, "r") as f:
            for line in parser.parse(f.readlines()):
                self.settings.update(line)

    def get_result_functions(self):
        base_results = super(PwscfParser, self).get_result_functions()
        base_results["One-electron energy contribution"] = "get_one_electron_energy_contribution"
        base_results["Hartree energy contribution"] = "get_hartree_energy_contribution"
        base_results["Exchange-correlation energy contribution"] = "get_xc_energy_contribution"
        base_results["Ewald energy contribution"] = "get_ewald_energy_contribution"
        return base_results

    def get_name(self): return "PWSCF"

    def _get_key_with_units(self, key):
        if key not in self.settings:
            return None
        return Property(scalars=[Scalar(value=self.settings[key])], units=self.settings["{} units".format(key)])

    def _get_line(self, search_string, search_file, return_string=True, case_sens=True):
        '''Return the first line containing a set of strings in a file.

        If return_string is False, we just return whether such a line
        was found. If case_sens is False, the search is case
        insensitive.

        '''
        if os.path.isfile(search_file):
            # if single search string
            if type(search_string) == type(''): search_string = [search_string]
            # if case insensitive, convert everything to lowercase
            if not case_sens: search_string = [i.lower() for i in search_string]
            with open(search_file) as fp:
                # search for the strings line by line
                for line in fp:
                    query_line = line if case_sens else line.lower()
                    if all([i in query_line for i in search_string]):
                        return line if return_string else True
                if return_string:
                    raise Exception('%s not found in %s'%(' & '.join(search_string), search_file))
                else: return False
        else: raise Exception('%s file does not exist'%search_file)

    def get_version_number(self):
        '''Determine the version number from the output'''
        return self.settings["version"]

    def get_xc_functional(self):
        '''Determine the xc functional from the output'''
        return Value(scalars=[Scalar(value=" ".join(self.settings["exchange-correlation"]))])

    def get_cutoff_energy(self):
        '''Determine the cutoff energy from the output'''
        return Value(
            scalars=[Scalar(value=self.settings["kinetic-energy cutoff"])],
            units=self.settings['kinetic-energy cutoff units']
        )

    def get_total_energy(self):
        '''Determine the total energy from the output'''
        return self._get_key_with_units("total energy")

    @Value_if_true
    def is_relaxed(self):
        '''Determine if relaxation run from the output'''
        return self._get_line('Geometry Optimization', self.outputf, return_string=False)

    def _is_converged(self):
        '''Determine if calculation converged; for a relaxation (static) run
        we look for ionic (electronic) convergence in the output'''
        if self.is_relaxed():
            # relaxation run case
            return self._get_line(['End of', 'Geometry Optimization'], self.outputf, return_string=False)
        else:
            # static run case
            return self._get_line('convergence has been achieved', self.outputf, return_string=False)

    def get_KPPRA(self):
        '''Determine the no. of k-points in the BZ (from the input) times the
        no. of atoms (from the output)'''
        # Find the no. of k-points
        fp = open(self.inputf).readlines()
        for l,ll in enumerate(fp):
            if "K_POINTS" in ll:
                # determine the type of input
                if len(ll.split()) > 1:
                    if "gamma" in ll.split()[1].lower():
                        ktype = 'gamma'
                    elif "automatic" in ll.split()[1].lower():
                        ktype = 'automatic'
                    else:
                        ktype = ''
                else: ktype = ''
                if ktype == 'gamma':
                    # gamma point:
                    # K_POINTS {gamma}
                    nk = 1
                elif ktype == 'automatic':
                    # automatic:
                    # K_POINTS automatic
                    #  12 12 1 0 0 0
                    line = [int(i) for i in fp[l+1].split()[0:3]]
                    nk = line[0]*line[1]*line[2]
                else:
                    # manual:
                    # K_POINTS
                    #  3
                    #  0.125  0.125  0.0  1.0
                    #  0.125  0.375  0.0  2.0
                    #  0.375  0.375  0.0  1.0
                    nk = 0
                    for k in range(int(fp[l+1].split()[0])):
                        nk += int(float(fp[l+2+k].split()[3]))
                # Find the no. of atoms
                natoms = int(self._get_line('number of atoms/cell', self.outputf).split()[4])
                return Value(scalars=[Scalar(value=nk*natoms)])
        fp.close()
        raise Exception('%s not found in %s'%('KPOINTS',self.inputf))

    @Value_if_true
    def uses_SOC(self):
        '''Looks for line with "with spin-orbit" in the output'''
        return self._get_line('with spin-orbit', self.outputf, return_string=False)

    def get_pp_name(self):
        '''Determine the pseudopotential names from the output'''
        ppnames = []
        # Find the number of atom types
        natomtypes = int(self._get_line('number of atomic types', self.outputf).split()[5])
        # Find the pseudopotential names
        with open(self.outputf) as fp:
            for line in fp:
                if "PseudoPot. #" in line:
                    ppnames.append(Scalar(value=next(fp).split('/')[-1].rstrip()))
                    if len(ppnames) == natomtypes:
                        return Value(scalars=ppnames)
            raise Exception('Could not find %i pseudopotential names'%natomtypes)

    def get_U_settings(self):
        '''Determine the DFT+U type and parameters from the output'''
        with open(self.outputf) as fp:
            for line in fp:
                if "LDA+U calculation" in line:
                    U_param = {}
                    U_param['Type'] = line.split()[0]
                    U_param['Values'] = {}
                    # look through next several lines
                    for nl in range(15):
                        line2 = next(fp).split()
                        if len(line2) > 1 and line2[0] == "atomic":
                            pass # column titles
                        elif len(line2) == 6:
                            U_param['Values'][line2[0]] = {}
                            U_param['Values'][line2[0]]['L'] = float(line2[1])
                            U_param['Values'][line2[0]]['U'] = float(line2[2])
                            U_param['Values'][line2[0]]['J'] = float(line2[4])
                        else: break # end of data block
                    return Value(**U_param)
            return None

    def get_vdW_settings(self):
        '''Determine the vdW type if using vdW xc functional or correction
        scheme from the input otherwise'''
        xc = self.get_xc_functional().scalars[0].value
        if 'vdw' in xc.lower(): # vdW xc functional
            return Value(scalars=[Scalar(value=xc)])
        else:
            # look for vdw_corr in input
            vdW_dict = {'xdm':'Becke-Johnson XDM', 'ts':
                        'Tkatchenko-Scheffler', 'ts-vdw':
                        'Tkatchenko-Scheffler',
                        'tkatchenko-scheffler':
                        'Tkatchenko-Scheffler', 'grimme-d2': 'Grimme D2', 'dft-d': 'Grimme D2'}
            if self._get_line('vdw_corr', self.inputf, return_string=False, case_sens=False):
                line = self._get_line('vdw_corr', self.inputf, return_string=True, case_sens=False)
                vdwkey = str(line.split('=')[-1].replace("'", "").replace(',', '').lower().rstrip())
                return Value(scalars=[Scalar(value=vdW_dict[vdwkey])])
            return None

    def get_pressure(self):
        '''Determine the pressure from the output'''
        return self._get_key_with_units("pressure")

    def get_stresses(self):
        '''Determine the stress tensor from the output'''
        if "stress" not in self.settings:
            return None
        wrapped = [[Scalar(value=x) for x in y] for y in self.settings["stress"]]
        return Property(matrices=[wrapped], units=self.settings["stress units"])

    def get_output_structure(self):
        '''Determine the structure from the output'''
        bohr_to_angstrom = 0.529177249

        # determine the number of atoms
        natoms = int(float(self._get_line('number of atoms/cell', self.outputf).split('=')[-1]))

        # determine the initial lattice parameter
        alat = float(self._get_line('lattice parameter (alat)', self.outputf).split('=')[-1].split()[0])

        # find the initial unit cell
        unit_cell = []
        with open(self.outputf, 'r') as fp:
            for line in fp:
                if "crystal axes:" in line:
                    for i in range(3):
                        unit_cell.append([float(j)*alat*bohr_to_angstrom for j in next(fp).split('(')[-1].split(')')[0].split()])
                    break
            if len(unit_cell) == 0: raise Exception('Cannot find the initial unit cell')

        # find the initial atomic coordinates
        coords = [] ; atom_symbols = []
        with open(self.outputf, 'r') as fp:
            for line in fp:
                if "site n." in line and "atom" in line and "positions" in line and "alat units" in line:
                    for i in range(natoms):
                        coordline = next(fp)
                        atom_symbols.append(''.join([i for i in coordline.split()[1] if not i.isdigit()]))
                        coord_conv_factor = alat*bohr_to_angstrom
                        coords.append([float(j)*coord_conv_factor for j in coordline.rstrip().split('=')[-1].split('(')[-1].split(')')[0].split()])
                    break
            if len(coords) == 0: raise Exception('Cannot find the initial atomic coordinates')

        if type(self.is_relaxed()) == type(None):
            # static run: create, populate, and return the initial structure
            structure = Atoms(symbols=atom_symbols, cell=unit_cell, pbc=True)
            structure.set_positions(coords)
            return structure
        else:
            # relaxation run: update with the final structure
            with open(self.outputf) as fp:
                for line in fp:
                    if "Begin final coordinates" in line:
                        if 'new unit-cell volume' in next(fp):
                            # unit cell allowed to change
                            next(fp) # blank line
                            # get the final unit cell
                            unit_cell = []
                            cellheader = next(fp)
                            if 'bohr' in cellheader.lower():
                                cell_conv_factor = bohr_to_angstrom
                            elif 'angstrom' in cellheader.lower():
                                cell_conv_factor = 1.0
                            else:
                                alat = float(cellheader.split('alat=')[-1].replace(')', ''))
                                cell_conv_factor = alat*bohr_to_angstrom
                            for i in range(3):
                                unit_cell.append([float(j)*cell_conv_factor for j in next(fp).split()])
                            next(fp) # blank line

                        # get the final atomic coordinates
                        coordtype = next(fp).split()[-1].replace('(', '').replace(')', '')
                        if coordtype == 'bohr':
                            coord_conv_factor = bohr_to_angstrom
                        elif coordtype == 'angstrom' or coordtype == 'crystal':
                            coord_conv_factor = 1.0
                        else:
                            coord_conv_factor = alat*bohr_to_angstrom
                        coords = [] # reinitialize the coords
                        for i in range(natoms):
                            coordline = next(fp).split()
                            coords.append([float(j)*coord_conv_factor for j in coordline[1:4]])

                        # create, populate, and return the final structure
                        structure = Atoms(symbols=atom_symbols, cell=unit_cell, pbc=True)
                        if coordtype == 'crystal':
                            structure.set_scaled_positions(coords) # direct coord
                        else:
                            structure.set_positions(coords) # cartesian coord
                        return structure
                raise Exception('Cannot find the final coordinates')

    def get_dos(self):
        '''Find the total DOS shifted by the Fermi energy'''
        # find the dos file
        fildos = ''
        for f in self._files:
            with open(f, 'r') as fp:
                first_line = next(fp)
                if "E (eV)" in first_line and "Int dos(E)" in first_line:
                    fildos = f
                    ndoscol = len(next(fp).split())-2 # number of spin channels
                    fp.close()
                    break
                fp.close()
        if not fildos:
            return None # cannot find DOS

        # get the Fermi energy
        line = self._get_line('the Fermi energy is', self.outputf)
        efermi = float(line.split('is')[-1].split()[0])

        # grab the DOS
        energy = [] ; dos = []
        fp = open(fildos, 'r')
        next(fp) # comment line
        for line in fp:
            ls = line.split()
            energy.append(Scalar(value=float(ls[0])-efermi))
            dos.append(Scalar(value=sum([float(i) for i in ls[1:1+ndoscol]])))
        return Property(scalars=dos, units='number of states per unit cell', conditions=Value(name='energy', scalars=energy, units='eV'))

    def get_forces(self):
        if "forces" not in self.settings:
            return None
        wrapped = [[Scalar(value=x) for x in y] for y in self.settings['forces']]
        return Property(vectors=wrapped, units=self.settings['force units'])

    def get_total_force(self):
        if "total force" not in self.settings:
            return None
        return Property(scalars=[Scalar(value=self.settings['total force'])], units=self.settings['force units'])

    def get_outcar(self):
        return None

    def get_incar(self):
        return None

    def get_poscar(self):
        return None

    def get_band_gap(self):
        '''Compute the band gap from the DOS'''
        dosdata = self.get_dos()
        if type(dosdata) == type(None):
            return None # cannot find DOS
        else:
            energy = dosdata.conditions.scalars
            dos = dosdata.scalars
            step_size = energy[1].value - energy[0].value
            not_found = True ; l = 0 ; bot = 10**3 ; top = -10**3
            while not_found and l < len(dos):
                # iterate through the data
                e = float(energy[l].value)
                dens = float(dos[l].value)
                # note: dos already shifted by efermi
                if e < 0 and dens > 1e-3:
                    bot = e
                elif e > 0 and dens > 1e-3:
                    top = e
                    not_found = False
                l += 1
            if top < bot:
                raise Exception('Algorithm failed to find the band gap')
            elif top - bot < step_size*2:
                return Property(scalars=[Scalar(value=0)], units='eV')
            else:
                bandgap = float(top-bot)
                return Property(scalars=[Scalar(value=round(bandgap,3))], units='eV')

    def get_one_electron_energy_contribution(self):
        return self._get_key_with_units("one-electron energy contribution")

    def get_hartree_energy_contribution(self):
        return self._get_key_with_units("hartree energy contribution")

    def get_xc_energy_contribution(self):
        return self._get_key_with_units("xc energy contribution")

    def get_ewald_energy_contribution(self):
        return self._get_key_with_units("ewald energy contribution")
