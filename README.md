dfttopif
========
[![Build Status](https://travis-ci.org/CitrineInformatics/pif-dft.svg?branch=master)](https://travis-ci.org/CitrineInformatics/pif-dft)

A Python library for extracting the input settings and results from Density Functional Theory calculations, and then storing that data in pif format.

Requirements
------------

Python 2.7 or >=3.5, with dependencies listed in [requirements.txt](https://github.com/CitrineInformatics/pif-dft/blob/master/requirements.txt)

Installation
------------

`dfttopif` is published on [PyPI](https://pypi.python.org/pypi/dfttopif), so it can be installed with `pip`:
```shell
$ pip install dfttopif
```

Usage
-----

Option 1: Call the command line tool `dfttopif` provided in the binary directory, which takes the directory containing DFT results as its only option

```shell

./bin/dfttopif /path/to/calculation/
```

Option 2: Generate the pif object via the python API

```python

from dfttopif import directory_to_pif
data = directory_to_pif('/path/to/calculation/')
```

Currently supported DFT codes
-----------------------------

 - VASP (versions tested: 5.2.11, 5.3.2, 5.3.5)
 - PWSCF (Quantum Espresso) (versions tested: 4.3.2, 5.0, 5.4.0, 6.0, 6.4.1)

Development
-----------

`dfttopif` is a collaborative effort.  Contributions are welcome, both issues and pull requests.
This project follows [gitflow workflow](https://www.atlassian.com/git/tutorials/comparing-workflows#gitflow-workflow),
so please make PRs to the `develop` branch.

API documentation is maintained in the source code and hosted on [github pages](http://citrineinformatics.github.io/pif-dft/).
