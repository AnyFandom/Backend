#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import click

from Backend import main


@click.group()
def cli():
    pass


@cli.command()
def run():
    config_keys = ['access_key', 'refresh_key', 'ip_key', 'server_host',
                   'server_port', 'db_host', 'db_port', 'db_database',
                   'db_user', 'db_password', 'db_min_size', 'db_max_size']

    config = dict(server=dict(), db=dict())

    for k, v in os.environ.items():
        if k in config_keys:
            spl = k.split('_', 1)
            if spl[0] in ('server', 'db'):
                config[spl[0]][spl[1]] = v
            else:
                config[k] = v

            config_keys.remove(k)

    if config_keys:
        raise Exception(str(config_keys))

    main(config)


if __name__ == '__main__':
    cli()
