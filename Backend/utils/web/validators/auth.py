#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from .validators import JsonValidator, Field, string


register = JsonValidator(
    Field(True, 'username', string, mn=3, mx=64),
    Field(True, 'password', string, mn=8, mx=256)
)

login = register

refresh = JsonValidator(
    Field(True, 'refresh_token', string)
)

invalidate = login

change = JsonValidator(
    Field(True, 'username', string, mn=3, mx=8),
    Field(True, 'password', string, mn=8, mx=256),
    Field(True, 'new_password', string, mn=8, mx=256)
)
