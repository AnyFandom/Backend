#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import JsonValidator, Field, string


register = JsonValidator(
    Field(True, 'username', string, mn=3, mx=64),
    Field(True, 'password', string, mn=8, mx=256)
)

login = JsonValidator(
    Field(True, 'username', string),
    Field(True, 'password', string)
)

refresh = JsonValidator(
    Field(True, 'refresh_token', string)
)

invalidate = login

change = JsonValidator(
    Field(True, 'username', string),
    Field(True, 'password', string),
    Field(True, 'new_password', string, mn=8, mx=256)
)
