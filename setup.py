from setuptools import setup, find_packages

setup(
    name='dfttopif',
    version='0.1.8',
    description='Library for parsing Density Functional Theory calculations',
    url='https://github.com/CitrineInformatics/pif-dft',
    install_requires=[
        'ase',
        'pypif==1.1.6',
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
