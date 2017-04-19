#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Any, Callable

from aiohttp.web_request import Request

from ..exceptions import ValidationError, InvalidJson


class _ValErr(Exception):
    pass


def _check(statement: bool, text: str):
    if not statement:
        raise _ValErr(text)


def string(val: Any, mn: int=None, mx: int=None) -> str:
    _check(isinstance(val, str), 'Expected str, got %s' % type(val).__name__)
    if mn and mx:
        _check(
            mn <= len(val) <= mx,
            'Must be at least %i characters long and maximum of %i. got %i' % (
                mn, mx, len(val))
        )

    return val


def integer(val: Any) -> int:
    _check(isinstance(val, int), 'Expected int, got %s' % type(val).__name__)
    return val


def boolean(val: Any) -> bool:
    _check(isinstance(val, bool), 'Expected bool, got %s' % type(val).__name__)
    return val


class Field:
    def __init__(self, required: bool, name: str, func: Callable,
                 default: Any=None, **args) -> None:
        self.name = name

        self._req = required
        self._func = func
        self._args = args
        self._def = default

    def __call__(self, obj: dict):
        val = obj.get(self.name, None)

        _check(not (val is None and self._req), 'Field is required')
        if val is None:
            return self._def

        return self._func(val, **self._args)


class JsonValidator:
    def __init__(self, *fields: Field) -> None:
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

            resp[field.name] = parsed

        if errs:
            raise ValidationError(details=errs)

        return resp


async def get_body(request: Request, validator: JsonValidator):
    try:
        return validator(await request.json())
    except json.decoder.JSONDecodeError as exc:
        raise InvalidJson(details=str(exc))
