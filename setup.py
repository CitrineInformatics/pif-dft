from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='dfttopif',
    version='0.1.1',
    description='Library for parsing Density Functional Theory calculations',
    long_description=readme,
    url='https://github.com/CitrineInformatics/pif-dft',
    license=license,
    install_requires=[
        'ase',
        'pypif',
    ],
    packages=find_packages(exclude=('tests', 'docs'))
)
