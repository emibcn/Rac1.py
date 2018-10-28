#!/usr/bin/env python

'Rac1.py packaging setup'

from setuptools import setup

VERSION = (1, 0, 5)
__version__ = '.'.join([str(v) for v in VERSION])

setup(
    name='Rac1',
    version=__version__,
    description="Listen to Rac1 catalan radio station from its public podcasts",
    long_description=("Small script to listen to Rac1 catalan radio station "
                      "from its public podcasts at http://www.rac1.cat/a-la-carta"),
    author="Emilio del Giorgio",
    author_email="https://github.com/emibcn",
    url="https://github.com/emibcn/Rac1.py",
    license="GPLv3",
    platforms=["any"],
    py_modules=['Rac1'],
    scripts=["bin/Rac1"],
    install_requires=['requests', 'configargparse', 'parsedatetime'],
    include_package_data=True,
    classifiers=[
        "Environment :: Command line",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
