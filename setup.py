from setuptools import setup

setup(
    name = 'narrative',
    packages = ['.'],
    version = '0.0.1',
    description = 'A python library for computing narrative chains.',
    author='Mike Wojcieszek',
    author_email='mw2353@gmail.com',
    url='https://github.com/loswojos/NarrativeEvents',
    install_requires=[
        'corenlp',
    ]

)

