from pypif.obj.common.property import Property

from .base import DFTParser, Value_if_true
import os
from pypif.obj.common.value import Value

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
        '''Determine the version number in the Program PWSCF line'''
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
        '''Determine the xc functional from the Exchange-correlation line'''
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
        '''Determine the cutoff energy from the kinetic-energy cutoff line'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "kinetic-energy cutoff" in line:
                    cutoff = line.split()[3:]
                    return Value(scalars=float(cutoff[0]), units=cutoff[1])
            raise Exception('kinetic-energy cutoff line not found in output')

    def get_total_energy(self):
        '''Determine the total energy from the ! total energy line'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            # reading file backwards in case relaxation run
            for line in reversed(fp.readlines()):
                if "!" in line and "total energy" in line:
                    energy = line.split()[4:]
                    return Value(scalars=float(energy[0]), units=energy[1])
            raise Exception('! total energy line not found in output')

    @Value_if_true
    def is_relaxed(self):
        '''Determine if relaxation run from presence of Geometry Optimization line'''
        with open(os.path.join(self._directory, self.outputf)) as fp:
            for line in fp:
                if "Geometry Optimization" in line:
                    return True

    def _is_converged(self):
        '''Determine if calculation converged; for a relaxation (static) run
        we look for ionic (electronic) convergence'''
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
        '''Determine the no. of k-points in the BZ times the no. of atoms'''
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
