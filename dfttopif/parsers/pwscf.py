from pypif.obj.common.property import Property

from .base import DFTParser, Value_if_true
import os
from pypif.obj.common.value import Value
from ase import Atoms

class PwscfParser(DFTParser):
    '''
    Parser for PWSCF calculations
    '''
    
    def get_name(self): return "PWSCF"

    def _get_line(self, search_string, search_file, basedir=None, return_string=True, case_sens=True):
        '''Return the first line containing a set of strings in a file.

        If return_string is False, we just return whether such a line
        was found. If case_sens is False, the search is case
        insensitive.

        '''
        if basedir == None: basedir = self._directory # default
        if os.path.isfile(os.path.join(basedir, search_file)):
            # if single search string
            if type(search_string) == type(''): search_string = [search_string]
            # if case insensitive, convert everything to lowercase
            if not case_sens: search_string = [i.lower() for i in search_string]
            with open(os.path.join(basedir, search_file)) as fp:
                # search for the strings line by line
                for line in fp:
                    query_line = line if case_sens else line.lower()
                    if all([i in query_line for i in search_string]):
                        return line if return_string else True
                if return_string:
                    raise Exception('%s not found in %s'%(' & '.join(search_string),os.path.join(basedir, search_file)))
                else: return False
        else: raise Exception('%s file does not exist'%os.path.join(basedir, search_file))
    
    def test_if_from(self, directory):
        '''Look for PWSCF input and output files'''
        self.inputf = self.outputf = ''
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        for f in files:
            if self._get_line('Program PWSCF', f, basedir=directory, return_string=False):
                self.outputf = f
            elif self._get_line('&control', f, basedir=directory, return_string=False, case_sens=False):
                self.inputf = f
            if self.inputf and self.outputf: return True
        return False

    def get_version_number(self):
        '''Determine the version number from the output'''
        line = self._get_line('Program PWSCF', self.outputf)
        version = " ".join(line.split('start')[0].split()[2:]).lstrip('v.')
        # return Value(scalars=version)
        return version

    def get_xc_functional(self):
        '''Determine the xc functional from the output'''
        # the xc functional is described by 1 or 4 strings
        # SLA  PZ   NOGX NOGC ( 1 1 0 0 0)
        # SLA  PW   PBX  PBC (1434)
        # PBE ( 1  4  3  4 0 0)
        # PBE0 (6484)
        # HSE (14*4)
        xcstring = self._get_line('Exchange-correlation', self.outputf).split()[2:6]
        for word in range(4):
            if xcstring[word][0] == '(':
                xcstring = xcstring[:word]
                break
        return Value(scalars=" ".join(xcstring))

    def get_cutoff_energy(self):
        '''Determine the cutoff energy from the output'''
        cutoff = self._get_line('kinetic-energy cutoff', self.outputf).split()[3:]
        return Value(scalars=float(cutoff[0]), units=cutoff[1])

    def get_total_energy(self):
        '''Determine the total energy from the output'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            # reading file backwards in case relaxation run
            for line in reversed(fp.readlines()):
                if "!" in line and "total energy" in line:
                    energy = line.split()[4:]
                    return Property(scalars=float(energy[0]), units=energy[1])
            raise Exception('%s not found in %s'%('! & total energy',os.path.join(self._directory, self.outputf)))

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
        fp = open(os.path.join(self._directory, self.inputf)).readlines()
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
                return Value(scalars=nk*natoms)
        fp.close()
        raise Exception('%s not found in %s'%('KPOINTS',os.path.join(self._directory, self.inputf)))

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
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "PseudoPot. #" in line:
                    ppnames.append(next(fp).split('/')[-1].rstrip())
                    if len(ppnames) == natomtypes:
                        return Value(scalars=ppnames)
            raise Exception('Could not find %i pseudopotential names'%natomtypes)

    def get_U_settings(self):
        '''Determine the DFT+U type and parameters from the output'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
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
            return Value(scalars=xc)
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
                return Value(scalars=vdW_dict[vdwkey])
            return None

    def get_pressure(self):
        '''Determine the pressure from the output'''
        if self._get_line('total   stress', self.outputf, return_string=False) == False:
            return None
        else:
            line = self._get_line('total   stress', self.outputf)
            # total   stress  (Ry/bohr**3)                   (kbar)     P=   -2.34
            # P= runs into the value if very large pressure
            pvalue = float(line.split()[-1].replace('P=', ''))
            return Property(scalars=pvalue, units='kbar')

    def get_stresses(self):
        '''Determine the stress tensor from the output'''
        stress_data = [] # stress tensor at each iteration
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "total" in line and "stress" in line:
                    stress = []
                    for i in range(3):
                        stress.append([float(j) for j in next(fp).split()[3:6]])
                    stress_data.append(stress)
            if len(stress_data) > 0:
                # return the final stress tensor
                return Property(matrices=stress_data[-1], units='kbar')
            else: return None

    def get_output_structure(self):
        '''Determine the structure from the output'''
        bohr_to_angstrom = 0.529177249

        # determine the number of atoms
        natoms = int(float(self._get_line('number of atoms/cell', self.outputf).split('=')[-1]))

        # determine the initial lattice parameter
        alat = float(self._get_line('lattice parameter (alat)', self.outputf).split('=')[-1].split()[0])

        # find the initial unit cell
        unit_cell = []
        with open(os.path.join(self._directory, self.outputf), 'r') as fp:
            for line in fp:
                if "crystal axes:" in line:
                    for i in range(3):
                        unit_cell.append([float(j)*alat*bohr_to_angstrom for j in next(fp).split('(')[-1].split(')')[0].split()])
                    break
            if len(unit_cell) == 0: raise Exception('Cannot find the initial unit cell')

        # find the initial atomic coordinates
        coords = [] ; atom_symbols = []
        with open(os.path.join(self._directory, self.outputf), 'r') as fp:
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
            with open(os.path.join(self._directory, self.outputf)) as fp:
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
        files = [f for f in os.listdir(self._directory) if os.path.isfile(os.path.join(self._directory, f))]
        for f in files:
            fp = open(os.path.join(self._directory, f), 'r')
            first_line = next(fp)
            if "E (eV)" in first_line and "Int dos(E)" in first_line:
                fildos = f
                ndoscol = len(next(fp).split())-2 # number of spin channels
                fp.close()
                break
            fp.close()
        if not fildos: return None # cannot find DOS

        # get the Fermi energy
        line = self._get_line('the Fermi energy is', self.outputf)
        efermi = float(line.split('is')[-1].split()[0])

        # grab the DOS
        energy = [] ; dos = []
        fp = open(os.path.join(self._directory, fildos), 'r')
        next(fp) # comment line
        for line in fp:
            ls = line.split()
            energy.append(float(ls[0])-efermi)
            dos.append(sum([float(i) for i in ls[1:1+ndoscol]]))
        return Property(scalars=dos, units='number of states per unit cell', conditions=Value(name='energy', scalars=energy, units='eV'))

    def get_forces(self):
        return None

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
                return Property(scalars=0, units='eV')
            else:
                bandgap = float(top-bot)
                return Property(scalars=round(bandgap,3), units='eV')
