from .parsers import VaspParser
from pypif import pif
from pypif.obj import *

def directory_to_pif(directory, verbose=0):
    '''Given a directory that contains output from
    a DFT calculation, parse the data and return
    a pif object

    Input:
        directory - String, path to directory containing
            DFT results
        verbose - int, How much status messages to print

    Output:
        pif - ChemicalSystem, Results and settings of
            the DFT calculation in pif format
    '''

    # For now, just create a VASP parser
    parser = VaspParser(directory)
    if not parser.test_if_from(directory):
        raise Exception('Directory is not in correct format')
    if verbose > 0:
        print("Found a %s directory", parser.get_name())
        
    # Get software information, to list as method
    software = Software(name=parser.get_name(),
        version=parser.get_version())
        
    # Define the DFT method object
    method = Method(name='Density Functional Theory',
        software=software)
        
    # Get the properties of the system
    property_methods = dict(
        Energy=parser.get_total_energy,
    ) # LW 27May16: Consider making this dictionary automatically update with new
    properties = []
    for name,func for properties.iteritems():
        try:
            prop = Property(name=name, 
    
    # 

    


    return None
