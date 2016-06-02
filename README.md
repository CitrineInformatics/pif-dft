dfttopif
========
[![Build Status](https://travis-ci.com/WardLT/pif-dft.svg?token=vC5kuseMWnCyTUzLrqNu&branch=master)](https://travis-ci.com/WardLT/pif-dft)

A Python library for extracting the input settings and results from Density Functional Theory calculations, and then storing that data in pif format.

Requirements
------------

Python 2.7, with dependencies listed in [requirements.txt](https://github.com/WardLT/pif-dft/blob/master/requirements.txt)

Installation
------------

First, install the packages with `pip install -r requirements.txt`, then call `python setup.py install`

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
