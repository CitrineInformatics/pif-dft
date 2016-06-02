from .parsers import VaspParser
from pypif import pif
from pypif.obj import *
import sys

def _assign_value(obj, t, value):
    '''Given a pypif Value object, set the approriate value according
    to the type of provided data
    
    Input:
        obj - Value object to be set
        t - String, Type of the data. Acceptable types:
            None <- No value is set
            scalar <- 0 dimensional data
            vector <- 1 dimensional data
            matrix <- 2 dimensional data
            tag <- Strings, or other objects
        value - Value to be set. If type is not None or tag,
            this must be a type where [0] is the value(s)
            and [1] is the units. For tag, this should be
            a string or list of strings
    '''
    print t, value
    if t is None or t.lower() == 'none':
        pass
    elif t.lower() == 'scalar':
        obj.scalers, obj.units = value
    elif t.lower() == 'vector':
        obj.vectors, obj.units = value
    elif t.lower() == 'matrix':
        obj.matrices, obj.units = value
    elif t.lower() == 'tag':
        obj.tags = str(value)
    else: 
        raise Exception('Type not supported: ' + str(t))
    return obj

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
    for name,(func,t) in parser.get_setting_functions().iteritems():
        # Get the condition
        cond = Value(name=name)
        func = getattr(parser, func)
        value = func()
        
        # If the condition is None or False, skip it
        if value is None or value == False:
            continue

        # Set the types
        _assign_value(cond, t, value)
        conditions.append(cond)
    
    # Get the properties of the system
    chem.properties = []
    for name,(func,t) in parser.get_result_functions().iteritems():
        # Get the property
        prop = Property(name=name, method=method, \
                data_type='COMPUTATIONAL', conditions=conditions)
        func = getattr(parser, func)
        value = func()
        
        # If the property is None, skip it
        if value is None:
            continue
        
        # Set the value
        _assign_value(prop, t, value)
        
        # Add it to the output
        chem.properties.append(prop)

    return chem
