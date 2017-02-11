#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path, pathsep, getenv
import errno

import click
from configobj import ConfigObj
from validate import Validator, ValidateError

from .main import main

spec = """[server]
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
    """Read config and run backend"""
    if config_path is None:
        path_list = list()
        path_list.append(path.join(
            getenv('XDG_CONFIG_HOME', path.expanduser('~/.config')), 'backend'
        ))
        for p in getenv('XDG_CONFIG_DIRS', '/etc/xdg').split(pathsep):
            path_list.append(path.join(p, 'backend'))

        for p in path_list:
            if path.isfile(path.join(p, 'config.ini')):
                config_path = path.join(p, 'config.ini')
                break
        else:
            msg = 'Can\'t find config.ini in any of these directories: ' + \
                  ', '.join(path_list)
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
