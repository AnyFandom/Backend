#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import JsonValidator, Field, string, integer

patch = JsonValidator(
    Field(True, 'id', integer),
    Field(False, 'description', string, mn=0, mx=65535),
    Field(False, 'avatar', string, mn=0, mx=64)
)
