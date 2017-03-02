#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Any
from types import FunctionType

from aiohttp.web_reqrep import Request

from .exceptions import ValidationError, InvalidJson


class _ValErr(Exception):
    pass


def _check(statement: bool, text: str):
    if not statement:
        raise _ValErr(text)


def string(val: Any, mn: int, mx: int) -> str:
    _check(isinstance(val, str), 'Expected str, got %s' % type(val).__name__)
    _check(mn <= len(val) <= mx,
           'Must be longer then %i characters and shorter then %i. got %i' % (
               mn, mx, len(val)))

    return val


class Field:
    def __init__(self, required: bool, name: str, func: FunctionType, **args):
        self.name = name

        self._req = required
        self._func = func
        self._args = args

    def __call__(self, obj: dict):
        val = obj.get(self.name, None)

        _check(not (val is None and self._req), 'Field is required')
        if val is None:
            return val

        return self._func(val, **self._args)


class JsonValidator:
    def __init__(self, *fields: Field):
        self._f = fields

    def __call__(self, obj: dict) -> dict:
        resp = dict()
        errs = list()

        for field in self._f:
            try:
                parsed = field(obj)
            except _ValErr as exc:
                errs.append('%s: %s' % (field.name, str(exc)))
                continue

            if parsed is None:
                continue

            resp[field.name] = parsed

        if errs:
            raise ValidationError(details=errs)

        return resp


register_validator = JsonValidator(
    Field(True, 'username', string, mn=3, mx=64),
    Field(True, 'password', string, mn=8, mx=256)
)


async def get_body(request: Request, validator: JsonValidator):
    try:
        return validator(await request.json())
    except json.decoder.JSONDecodeError as exc:
        raise InvalidJson(details=str(exc))
