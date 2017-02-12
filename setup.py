#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path, pathsep, getenv
from codecs import open
from setuptools import setup, find_packages

config_path = path.join(
    getenv('XDG_CONFIG_DIRS', '/etc/xdg').split(pathsep)[0], 'backend')

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
        'uvloop==0.8.0',
        'aiohttp==1.3.1',
        'asyncpg==0.8.4',
        'configobj==5.0.6'
    ],

    data_files=[(config_path, ['Backend/config.ini'])],
    entry_points={'console_scripts': ['backend=Backend.__main__:cli']},

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Operating System :: POSIX'
        'Programming Language :: Python :: 3.6',
    ]
)
