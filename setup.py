from setuptools import setup, find_packages

setup(
    name='dfttopif',
    version='0.1.7',
    description='Library for parsing Density Functional Theory calculations',
    url='https://github.com/CitrineInformatics/pif-dft',
    install_requires=[
        'ase',
        'pypif',
    ],
    packages=find_packages(exclude=('tests', 'docs'))
)
