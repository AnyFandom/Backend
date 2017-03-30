#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from .gen import encode, decode
from ..exceptions import ExpiredToken


def encode_timed(fmt: str, *val, key: bytes, life: int) -> bytes:
    return encode('I' + fmt, int(time.time()) + life, *val, key=key)


def decode_timed(token: bytes, *, key: bytes) -> tuple:
    decoded = decode(token, key=key)

    if decoded[0] < time.time():
        raise ExpiredToken

    return decoded[1:]
