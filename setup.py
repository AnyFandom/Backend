#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path
from codecs import open
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='anyfandom_backend',
    version='0.1.0.dev',
    long_description=long_description,

    packages=find_packages(),
    install_requires=[
        'click==6.7',
    ],

    entry_points={'console_scripts': ['backend=Backend.__main__:cli']},

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: Russian',
        'Operating System :: POSIX'
        'Programming Language :: Python :: 3.6',
    ]
)
