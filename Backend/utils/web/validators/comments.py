#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import Validator, Field, string, boolean


insert = Validator(
    Field(True, 'content', string, mn=8, mx=65535)
)

update = Validator(
    Field(False, 'content', string, mn=8, mx=65535)
)

votes_insert = Validator(
    Field(True, 'vote', boolean)
)
