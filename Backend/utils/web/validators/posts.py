#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import JsonValidator, Field, string


insert = JsonValidator(
    Field(True, 'title', string, mn=8, mx=128),
    Field(True, 'content', string, mn=8, mx=65535)
)

update = JsonValidator(
    Field(False, 'title', string, mn=8, mx=128),
    Field(False, 'content', string, mn=8, mx=65535)
)
