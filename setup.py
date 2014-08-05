from setuptools import setup

setup(
    name = 'narrative',
    packages = ['narrative'],
    version = '0.0.5',
    description = 'A python library for building narrative chains.',
    author='Michael Wojcieszek',
    author_email='mw2353@gmail.com',
    url='https://github.com/loswojos/NarrativeEvents',
    install_requires=[
        'corenlp',
    ]

)

