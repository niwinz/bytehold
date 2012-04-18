# -*- coding: utf-8 -*-

#from distutils.core import setup
from setuptools import setup, find_packages
from bytehold import __version__ as version

setup(
    name = "bytehold",
    version = "{v[0]}.{v[1]}".format(v=version),
    description = "Simple backup tool, which helps not to repeat scripts.",
    author = "Andrei Antoukh",
    author_email = "niwi@niwi.be",
    url = "https://github.com/niwibe/bytehold",
    py_modules = ["bytehold"],
    scripts = ['bh'],
    license = "BSD",
    classifiers = [
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Systems Administration',
    ],
)
