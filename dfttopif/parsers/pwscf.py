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
    
    def test_if_from(self,directory):
        '''Look for PWSCF input and output files based on &control and Program
        PWSCF, respectively'''
        self.inputf=self.outputf=''
        maxlines = 15
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        for f in files:
            fp = open(os.path.join(directory, f), 'r')
            for l in range(maxlines):
                line = fp.readline()
                if "Program PWSCF" in line:
                    self.outputf = f
                elif "&control" in line.lower():
                    self.inputf = f
            fp.close()
            if self.inputf and self.outputf: return True
        return False

    def get_version_number(self):
        '''Determine the version number from the output'''
        maxlines = 15
        fp = open(os.path.join(self._directory, self.outputf))
        for l in range(maxlines):
            line = fp.readline()
            if "Program PWSCF" in line:
                version = " ".join(line.split('start')[0].split()[2:]).lstrip('v.')
                fp.close()
                return Value(scalars=version)
        fp.close()
        raise Exception('Program PWSCF line not found in output')

    def get_xc_functional(self):
        '''Determine the xc functional from the output'''
        # the xc functional is described by 1 or 4 strings
        # SLA  PZ   NOGX NOGC ( 1 1 0 0 0)
        # SLA  PW   PBE  PBE ( 1  4  3  4 0 0)
        # SLA  PW   PBX  PBC (1434)
        # SLA  PW   TPSS TPSS (1476)
        # PBE ( 1  4  3  4 0 0)
        # PBE0 (6484)
        # VDW-DF (1449)
        # HSE (14*4)
        # LDA ( 1  1  0  0 0 0)
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "Exchange-correlation" in line:
                    xcstring = line.split()[2:6]
                    for word in range(4):
                        if xcstring[word][0] == '(':
                            xcstring=xcstring[:word]
                            break
                    return Value(scalars=" ".join(xcstring))
            raise Exception('Exchange-correlation line not found in output')

    def get_cutoff_energy(self):
        '''Determine the cutoff energy from the output'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "kinetic-energy cutoff" in line:
                    cutoff = line.split()[3:]
                    return Value(scalars=float(cutoff[0]), units=cutoff[1])
            raise Exception('kinetic-energy cutoff line not found in output')

    def get_total_energy(self):
        '''Determine the total energy from the output'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            # reading file backwards in case relaxation run
            for line in reversed(fp.readlines()):
                if "!" in line and "total energy" in line:
                    energy = line.split()[4:]
                    return Value(scalars=float(energy[0]), units=energy[1])
            raise Exception('! total energy line not found in output')

    @Value_if_true
    def is_relaxed(self):
        '''Determine if relaxation run from the output'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "Geometry Optimization" in line:
                    return True

    def _is_converged(self):
        '''Determine if calculation converged; for a relaxation (static) run
        we look for ionic (electronic) convergence in the output'''
        if self.is_relaxed():
            # relaxation run case
            with open(os.path.join(self._directory, self.outputf)) as fp:
                for line in fp:
                    if "End of" in line and "Geometry Optimization" in line:
                        return True
                return False
        else:
            # static run case
            with open(os.path.join(self._directory, self.outputf)) as fp:
                for line in fp:
                    if "convergence has been achieved" in line:
                        return True
                return False

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
                with open(os.path.join(self._directory, self.outputf)) as fp2:
                    for line in fp2:
                        if "number of atoms/cell" in line:
                            # number of atoms/cell      =           12
                            natoms = int(line.split()[4])
                            return Value(scalars=nk*natoms)
                    raise Exception('number of atoms/cell line not found in output')
        fp.close()
        raise Exception('K_POINTS line not found in input')

    @Value_if_true
    def uses_SOC(self):
        '''Looks for line with "with spin-orbit" in the output'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "with spin-orbit" in line:
                    return True

    def get_pp_name(self):
        '''Determine the pseudopotential names from the output'''
        ppnames=[]
        # Find the number of atom types
        natomtypes=0
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "number of atomic types" in line:
                    natomtypes=int(line.split()[5])
            if natomtypes == '':
                raise Exception('Number of atomic types not found in output')
        # Find the pseudopotential names
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "PseudoPot. #" in line:
                    ppnames.append(fp.next().split('/')[-1].rstrip())
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
                        line2=next(fp).split()
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
        xc=self.get_xc_functional().scalars
        if 'vdw' in xc.lower():
            # vdW xc functional
            return Value(scalars=xc)
        else:
            # look for vdw_corr in input
            vdW_dict = {'xdm':'Becke-Johnson XDM', 'ts':
                        'Tkatchenko-Scheffler', 'ts-vdw':
                        'Tkatchenko-Scheffler',
                        'tkatchenko-scheffler':
                        'Tkatchenko-Scheffler', 'grimme-d2': 'Grimme D2', 'dft-d': 'Grimme D2'}
            fp = open(os.path.join(self._directory, self.inputf)).readlines()
            for line in fp:
                if "vdw_corr" in line.lower():
                    vdwkey=str(line.split('=')[-1].replace("'", "").replace(',', '').lower().rstrip())
                    return Value(scalars=vdW_dict[vdwkey])
            return None

    def get_pressure(self):
        '''Determine the pressure from the output'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in reversed(fp.readlines()):
                if "total   stress" in line:
                    # total   stress  (Ry/bohr**3)                   (kbar)     P=   -2.34
                    # P= runs into the value if very large pressure
                    pvalue = float(line.split()[-1].replace('P=', ''))
                    return Value(scalars=pvalue, units='kbar')
            return None

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
        '''Determine the structure'''
        bohr_to_angstrom = float(0.529177249)

        # determine the number of atoms and initial lattice parameter
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "number of atoms/cell" in line:
                    natoms=int(float(line.split('=')[-1]))
                if "lattice parameter (alat)" in line:
                    alat=float(line.split('=')[-1].split()[0])
            if not natoms:
                raise Exception('Cannot find the number of atoms')
            elif not alat:
                raise Exception('Cannot find the lattice parameter')

        # find the initial unit cell
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "crystal axes:" in line:
                    unit_cell = []
                    for i in range(3):
                        unit_cell.append([float(j)*alat*bohr_to_angstrom for j in fp.next().split('(')[-1].split(')')[0].split()])
                    break
            if not unit_cell: raise Exception('Cannot find the initial unit cell')

        # find the initial atomic coordinates
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "site n." in line and "atom" in line and "positions" in line and "alat units" in line:
                    coords = [] ; atom_symbols = []
                    for i in range(natoms):
                        coordline = fp.next()
                        atom_symbols.append(''.join([i for i in coordline.split()[1] if not i.isdigit()]))
                        coord_conv_factor = alat*bohr_to_angstrom
                        coords.append([float(j)*coord_conv_factor for j in coordline.rstrip().split('=')[-1].split('(')[-1].split(')')[0].split()])
                    break
            if not coords: raise Exception('Cannot find the initial atomic coordinates')

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
                        if 'new unit-cell volume' in fp.next():
                            # unit cell allowed to change
                            for i in range(1): fp.next() # blank line

                            # get the final unit cell
                            unit_cell = []
                            cellheader = fp.next()
                            if 'bohr' in cellheader.lower():
                                cell_conv_factor = bohr_to_angstrom
                            elif 'angstrom' in cellheader.lower():
                                cell_conv_factor = 1.0
                            else:
                                alat = float(cellheader.split('alat=')[-1].replace(')', ''))
                                cell_conv_factor = alat*bohr_to_angstrom
                            for i in range(3):
                                unit_cell.append([float(j)*cell_conv_factor for j in fp.next().split()])

                            fp.next() # blank line

                        # get the final atomic coordinates
                        coordtype = fp.next().split()[-1].replace('(', '').replace(')', '')
                        if coordtype == 'bohr':
                            coord_conv_factor = bohr_to_angstrom
                        elif coordtype == 'angstrom' or coordtype == 'crystal':
                            coord_conv_factor = 1.0
                        else:
                            coord_conv_factor = alat*bohr_to_angstrom
                        coords = [] # reinitialize the coords
                        for i in range(natoms):
                            coordline = fp.next().split()
                            coords.append([float(j)*coord_conv_factor for j in coordline[1:4]])

                        # create, populate, and return the final structure
                        structure = Atoms(symbols=atom_symbols, cell=unit_cell, pbc=True)
                        if coordtype == 'crystal':
                            # direct coordinates
                            structure.set_scaled_positions(coords)
                        else:
                            # cartesian coordinates
                            structure.set_positions(coords)
                        return structure

                raise Exception('Cannot find the final coordinates')
