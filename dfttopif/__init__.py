import os
import uuid
import tarfile
import shutil
from dfttopif.parsers import VaspParser
from dfttopif.parsers import PwscfParser
from pypif.obj import *


def tarfile_to_pif(filename, temp_root_dir='', verbose=0):
    """
    Process a tar file that contains DFT data.

    Input:
        filename - String, Path to the file to process.
        temp_root_dir - String, Directory in which to save temporary files. Defaults to working directory.
        verbose - int, How much status messages to print

    Output:
        pif - ChemicalSystem, Results and settings of
            the DFT calculation in pif format
    """
    temp_dir = temp_root_dir + str(uuid.uuid4())
    os.makedirs(temp_dir)
    try:
        tar = tarfile.open(filename, 'r')
        tar.extractall(path=temp_dir)
        tar.close()
        for i in os.listdir(temp_dir):
            cur_dir = temp_dir + '/' + i
            if os.path.isdir(cur_dir):
                return directory_to_pif(cur_dir, verbose)
        return directory_to_pif(temp_dir, verbose)
    finally:
        shutil.rmtree(temp_dir)


def archive_to_pif(filename, verbose=0):
    """
    Given a archive file that contains output from a DFT calculation, parse the data and return a PIF object.

    Input:
        filename - String, Path to the file to process.
        verbose - int, How much status messages to print

    Output:
        pif - ChemicalSystem, Results and settings of
            the DFT calculation in pif format
    """
    if tarfile.is_tarfile(filename):
        return tarfile_to_pif(filename, verbose)
    raise Exception('Cannot process file type')


def directory_to_pif(directory, verbose=0, quality_report=False):
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
    chem.chemical_formula = parser.get_composition()
        
    # Get software information, to list as method
    software = Software(name=parser.get_name(),
        version=parser.get_version_number())
        
    # Define the DFT method object
    method = Method(name='Density Functional Theory',
        software=software)
        
    # Get the settings (aka. "conditions") of the DFT calculations
    conditions = []
    for name, func in parser.get_setting_functions().items():
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
    for name, func in parser.get_result_functions().items():
        # Get the property
        prop = getattr(parser, func)()
        
        # If the property is None, skip it
        if prop is None:
            continue

        # Add name and other data
        prop.name = name
        prop.method = method
        prop.data_type='COMPUTATIONAL'
        if verbose > 0 and isinstance(prop, Value):
            print(name)
        if prop.conditions is None:
            prop.conditions = conditions
        else:
            if not isinstance(prop.conditions, list):
                prop.conditions = [prop.conditions]
            prop.conditions.extend(conditions)

        # Add it to the output
        chem.properties.append(prop)

    if quality_report:
        import tarfile
        tar = tarfile.open("tmp.tar", "w")
        tar.add(os.path.join(directory, "OUTCAR"))
        tar.add(os.path.join(directory, "INCAR"))
        tar.close()

        import requests
        r = requests.post('https://calval.citrination.com/validate/tarfile', data=open('tmp.tar', 'rb').read())
        os.remove("tmp.tar")

        if r.status_code == requests.codes.ok:
            report = r.json()[0]
            score = int(report.split('\n')[0].split()[-1]) # the score is the last token on the first line
            report_file = os.path.join(directory, "quality_report.txt")
            with open(report_file, "w") as f:
                f.write(report)
            if report_file[0:2] == "./":
                report_file = report_file[2:]
            chem.properties.append(
                    Property(
                        name="quality_report",
                        scalars=[Scalar(value=score)],
                        files=[FileReference(relative_path=report_file)]
                    )
                )
        else:
            print("Something failed: {}".format(r.status_code))
            print(r.status_code)

    return chem
