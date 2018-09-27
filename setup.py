from setuptools import setup, find_packages

setup(
    name='dfttopif',
    version='1.0.0',
    description='Library for parsing Density Functional Theory calculations',
    url='https://github.com/CitrineInformatics/pif-dft',
    install_requires=[
        'ase',
        'pypif>=2.0.1,<3',
        'dftparse>=0.2.1'
    ],
    extras_require={
        'report': ["requests"],
    },
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={
        'citrine.dice.converter': [
            'dft = dfttopif'
        ]
    }
)
