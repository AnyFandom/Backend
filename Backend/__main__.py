#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import errno

import click
from configobj import ConfigObj
from validate import Validator, ValidateError

from .main import main

spec = """access_key = string()
refresh_key = string()
ip_key = string()

[server]
host = string()
port = integer()

[db]
host = string(default=None)
port = integer(default=None)
database = string()

user = string(default=None)
password = string(default=None)

min_size = integer(min=1)
max_size = integer(min=1)
""".splitlines()


@click.group()
def cli():
    pass


@cli.command()
@click.option('-C', '--config_path', type=click.Path())
@click.option('-P', '--port', type=int)
def run(config_path, port):
    if config_path is None:
        path_list = [
            os.path.join(x, 'backend') for x in [
                os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config')),
                *os.getenv('XDG_CONFIG_DIRS', '/etc/xdg').split(os.pathsep)
            ]
        ]

        for p in path_list:
            if os.path.isfile(os.path.join(p, 'config.ini')):
                config_path = os.path.join(p, 'config.ini')
                break
        else:
            msg = 'Can\'t find config.ini in any of these directories: ' + \
                  ', '.join(path_list)
            raise FileNotFoundError(errno.ENOENT, msg)
    else:
        config_path = os.path.abspath(config_path)
        if not os.path.isfile(config_path):
            msg = 'No such file: ' + config_path
            raise FileNotFoundError(errno.ENOENT, msg)

    config = ConfigObj(config_path, configspec=spec)
    check = config.validate(Validator())
    if check is not True:
        msg = 'Invalid config file at %s: ' % config_path
        raise ValidateError(msg + str(check))

    if port is not None:
        config['server']['port'] = port

    main(dict(config))


if __name__ == '__main__':
    cli()
