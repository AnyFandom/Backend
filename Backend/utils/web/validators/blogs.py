#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import JsonValidator, Field, string, integer, boolean


insert = JsonValidator(
    Field(True, 'title', string, mn=3, mx=64),
    Field(True, 'url', string, mn=6, mx=32),
    Field(False, 'description', string, mn=0, mx=65535, default=''),
    Field(False, 'avatar', string, mn=0, mx=64, default='')
)

update = JsonValidator(
    Field(False, 'title', string, mn=3, mx=64),
    Field(False, 'description', string, mn=0, mx=65535),
    Field(False, 'avatar', string, mn=0, mx=64)
)

moders_insert = JsonValidator(
    Field(True, 'user_id', integer),
    Field(True, 'edit_b', boolean),
    Field(True, 'manage_b', boolean),
    Field(True, 'ban_b', boolean),
    Field(True, 'create_p', boolean),
    Field(True, 'edit_p', boolean),
    Field(True, 'edit_c', boolean),
)

moders_update = JsonValidator(
    Field(False, 'edit_b', boolean),
    Field(False, 'manage_b', boolean),
    Field(False, 'ban_b', boolean),
    Field(False, 'create_p', boolean),
    Field(False, 'edit_p', boolean),
    Field(False, 'edit_c', boolean),
)

bans_insert = JsonValidator(
    Field(True, 'user_id', integer),
    Field(True, 'reason', string, mn=0, mx=128),
)
