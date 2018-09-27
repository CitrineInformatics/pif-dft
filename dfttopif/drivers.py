import os
import uuid
import tarfile
import shutil
from dfttopif.parsers import VaspParser
from dfttopif.parsers import PwscfParser
from dfttopif.parsers.base import InvalidIngesterException
from pypif.obj import *
import json


def _add_quality_report(parser, pif, inline=True):
    import tarfile

    # if the parser lacks an INCAR, return None
    if parser.incar is None:
        return None

    # Create the tar file
    tar = tarfile.open("tmp.tar", "w")
    tar.add(parser.outcar, arcname="OUTCAR")
    tar.add(parser.incar, arcname="INCAR")
    tar.close()

    import requests
    if inline:
        r = requests.post('https://calval.citrination.com/validate/json/tarfile', data=open('tmp.tar', 'rb').read())
        report = json.loads(r.json()[0])
        score = report["score"]
    else:
        r = requests.post('https://calval.citrination.com/validate/tarfile', data=open('tmp.tar', 'rb').read())
        report = r.json()[0]
        score = int(report.split('\n')[0].split()[-1]) # the score is the last token on the first line
    os.remove("tmp.tar")

    if r.status_code != requests.codes.ok:
        print("Unable to generate quality report; request returned with status {}".format(r.status_code))
        return

    if inline:
        setattr(pif, "quality_report", report)
    else:
        report_file = os.path.join(os.path.dirname(parser.outcar), "quality_report.txt")
        with open(report_file, "w") as f:
            f.write(report)
        if report_file[0:2] == "./":
            report_file = report_file[2:]
        pif.properties.append(
                Property(
                    name="quality_report",
                    scalars=[Scalar(value=score)],
                    files=[FileReference(relative_path=report_file)]
                )
            )

    return pif


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
                return directory_to_pif(cur_dir, verbose=verbose)
        return directory_to_pif(temp_dir, verbose=verbose)
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


def files_to_pif(files, verbose=0, quality_report=True, inline=True):
    '''Given a directory that contains output from
    a DFT calculation, parse the data and return
    a pif object

    Input:
        files - [str] list of files from which the parser is allowed to read.
        verbose - int, How much status messages to print

    Output:
        pif - ChemicalSystem, Results and settings of
            the DFT calculation in pif format
    '''

    # Look for the first parser compatible with the directory
    found_parser = False
    for possible_parser in [PwscfParser, VaspParser]:
        try:
            parser = possible_parser(files)
            found_parser = True
            break
        except InvalidIngesterException:
            # Constructors fail when they cannot find appropriate files
            pass
    if not found_parser:
        raise Exception('Directory is not in correct format for an existing parser')
    if verbose > 0:
        print("Found a {} directory".format(parser.get_name()))
        
    # Get information about the chemical system
    chem = ChemicalSystem()
    chem.chemical_formula = parser.get_composition()
        
    # Get software information, to list as method
    software = Software(name=parser.get_name(),
        version=parser.get_version_number())
        
    # Define the DFT method object
    method = Method(name='Density Functional Theory',
        software=[software])
        
    # Get the settings (aka. "conditions") of the DFT calculations
    conditions = []
    for name, func in parser.get_setting_functions().items():
        # Get the condition
        cond = getattr(parser, func)()

        # If the condition is None or False, skip it
        if cond is None:
            continue

        if inline and cond.files is not None:
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

        if inline and prop.files is not None:
            continue

        # Add name and other data
        prop.name = name
        prop.methods = [method,]
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

    # Check to see if we should add the quality report
    if quality_report and isinstance(parser, VaspParser):
        _add_quality_report(parser, chem)

    return chem


def directory_to_pif(directory, **kwargs):
    """
    Convert a directory to a pif
    :param directory: Directory to convert to a pif
    :param kwargs: any additional keyword arguments. (See `files_to_pif`)
    :return: the created pif
    """

    # Get the files
    files = [os.path.join(directory, f) for f in os.listdir(directory)
             if os.path.isfile(os.path.join(directory, f))]

    # Run the pif
    return files_to_pif(files, **kwargs)


def convert(files, **kwargs):
    """
    Wrap directory to pif as a dice extension
    :param files: a list of files, which must be non-empty
    :param kwargs: any additional keyword arguments
    :return: the created pif
    """

    if len(files) < 1:
        raise ValueError("Files needs to be a non-empty list")

    if len(files) == 1:
        if os.path.isfile(files[0]):
            return files_to_pif(files, **kwargs)
        else:
            return directory_to_pif(files[0], **kwargs)
    else:
        return files_to_pif([x for x in files if os.path.isfile(x)], **kwargs)
