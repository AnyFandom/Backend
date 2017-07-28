#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import Validator, Field, string


register = Validator(
    Field(True, 'username', string, mn=3, mx=32),
    Field(True, 'password', string, mn=8, mx=256)
)

login = Validator(
    Field(True, 'username', string),
    Field(True, 'password', string)
)

refresh = Validator(
    Field(True, 'refresh_token', string)
)

invalidate = login

change = Validator(
    Field(True, 'username', string),
    Field(True, 'password', string),
    Field(True, 'new_password', string, mn=8, mx=256)
)
