
from setuptools import setup, find_packages

VERSION = (1, 0, 3)
__version__ = '.'.join(map(str, VERSION))

setup(
    name = 'Rac1',
    version = __version__,
    description = "Listen to Rac1 catalan radio station from its public podcasts",
    long_description = "Small script to listen to Rac1 catalan radio station from its public podcasts at http://www.rac1.cat/a-la-carta",
    author = "Emilio del Giorgio",
    author_email = "https://github.com/emibcn",
    url = "https://github.com/emibcn/Rac1.py",
    license = "GPLv3",
    platforms = ["any"],
    py_modules=['Rac1'],
    scripts = ["bin/Rac1"],
    install_requires = ['requests', 'argparse', 'parsedatetime'],
    include_package_data = True,
    classifiers = [
        "Environment :: Command line",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
