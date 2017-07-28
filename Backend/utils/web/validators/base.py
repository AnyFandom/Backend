#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .validators import Validator, Field, qinteger


page = Validator(
    Field(False, 'page', qinteger, default=0)
)
