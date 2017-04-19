#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import JsonValidator, Field, string


insert = JsonValidator(
    Field(True, 'title', string, mn=3, mx=64),
    Field(True, 'url', string, mn=6, mx=32),
    Field(False, 'description', string, mn=0, mx=65535, default=''),
    Field(False, 'avatar', string, mn=0, mx=64, default='')
)

patch = JsonValidator(
    Field(False, 'title', string, mn=3, mx=64),
    Field(False, 'description', string, mn=0, mx=65535),
    Field(False, 'avatar', string, mn=0, mx=64)
)
