#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click

from .main import main


@click.group()
def cli():
    pass


@cli.command()
def run():
    main()

if __name__ == '__main__':
    cli()
