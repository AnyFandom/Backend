#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hmac
import struct
from hashlib import sha1 as alg
from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode

from ..exceptions import InvalidToken


def b64d(s):
    try:
        return urlsafe_b64decode(s)
    except Exception:
        raise InvalidToken


def _sign(inp: bytes, key: bytes):
    return hmac.new(key, inp, alg).digest()


def encode(fmt: str, *val, key: bytes) -> bytes:
    body = b64e(struct.pack(fmt, *val))
    fmt_body = fmt.encode('utf-8') + b'.' + body
    sign = b64e(_sign(fmt_body, key))

    return fmt_body + b'.' + sign


def decode(token: bytes, *, key: bytes) -> tuple:
    segments = token.split(b'.')
    if len(segments) != 3:
        raise InvalidToken

    fmt, body, sign = segments

    if not hmac.compare_digest(b64d(sign), _sign(fmt + b'.' + body, key)):
        raise InvalidToken

    return struct.unpack(fmt.decode('utf-8'), b64d(body))
