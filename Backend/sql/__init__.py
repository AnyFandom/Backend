#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

init = open(os.path.dirname(os.path.abspath(__file__)) + '/init.sql').read()

__all__ = ('init',)
