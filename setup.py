from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='dfttopif',
    version='0.0.1',
    description='Library for parsing Density Functional Theory calculations',
    long_description=readme,
    url='https://github.com/CitrineInformatics/pif-dft',
    license=license,
    install_requires=[
        'ase',
        'pypif',
    ],
    dependency_links=['https://github.com/CitrineInformatics/pypif/zipball/master']
    packages=find_packages(exclude=('tests', 'docs'))
)
