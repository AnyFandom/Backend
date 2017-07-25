#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import Validator, Field, string, qinteger


select = Validator(
    Field(False, 'page', qinteger, default=0)
)

update = Validator(
    Field(False, 'description', string, mn=0, mx=65535),
    Field(False, 'avatar', string, mn=0, mx=64)
)
