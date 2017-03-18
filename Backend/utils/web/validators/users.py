#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import JsonValidator, Field, string


patch = JsonValidator(
    Field(False, 'description', string, mn=0, mx=65535, default=''),
    Field(False, 'avatar', string, mn=0, mx=64, default='')
)
