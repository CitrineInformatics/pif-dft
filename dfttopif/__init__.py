from .parsers import VaspParser
from .parsers import PwscfParser
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

    # Look for the first parser compatible with the directory
    foundParser = False
    for possible_parser in [VaspParser, PwscfParser]:
        try:
            parser = possible_parser(directory)
            if parser.test_if_from(directory):
                foundParser = True
                break
        except: pass
    if not foundParser:
        raise Exception('Directory is not in correct format for an existing parser')
    if verbose > 0:
        print("Found a %s directory", parser.get_name())
        
    # Get information about the chemical system
    chem = ChemicalSystem()
    chem.chemical_system = parser.get_composition()
        
    # Get software information, to list as method
    software = Software(name=parser.get_name(),
        version=parser.get_version_number())
        
    # Define the DFT method object
    method = Method(name='Density Functional Theory',
        software=software)
        
    # Get the settings (aka. "conditions") of the DFT calculations
    conditions = []
    for name, func in parser.get_setting_functions().iteritems():
        # Get the condition
        cond = getattr(parser, func)()

        # If the condition is None or False, skip it
        if cond is None:
            continue

        # Set the name
        cond.name = name

        # Set the types
        conditions.append(cond)
    
    # Get the properties of the system
    chem.properties = []
    for name, func in parser.get_result_functions().iteritems():
        # Get the property
        prop = getattr(parser, func)()
        
        # If the property is None, skip it
        if prop is None:
            continue

        # Add name and other data
        prop.name = name
        prop.method = method
        prop.data_type='COMPUTATIONAL'
        if isinstance(prop, Value):
            print name
        if prop.conditions is None:
            prop.conditions = conditions
        else:
            if not isinstance(prop.conditions, list):
                prop.conditions = [prop.conditions]
            prop.conditions.append(conditions)

        # Add it to the output
        chem.properties.append(prop)

    return chem
