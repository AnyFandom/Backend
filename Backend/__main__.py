#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click

from .main import main


@click.group()
def cli():
    pass


@cli.command()
@click.option('-H', '--host', type=str, default='localhost',
              help='TCP/IP hostname to serve on (default: localhost)')
@click.option('-P', '--port', type=int, default=8080,
              help='TCP/IP port to serve on (default: 8080)')
def run(host, port):
    """Run backend"""
    main(host, port)

if __name__ == '__main__':
    cli()
