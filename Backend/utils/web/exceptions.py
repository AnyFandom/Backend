#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import hdrs

from .response import JsonResponse


class JsonException(JsonResponse, Exception):
    status = None
    status_code = None
    description = None

    def __init__(self, *, headers=None, reason=None):
        body = {'code': type(self).__name__, 'description': self.description}

        JsonResponse.__init__(self, body=body, status=self.status,
                              headers=headers, reason=reason,
                              status_code=self.status_code)
        Exception.__init__(self)


class FailException(JsonException):
    status = 'fail'


class ResourceNotFound(FailException):
    status_code = 404
    description = 'The specified resource does not exists.'


class MethodNotAllowed(FailException):
    status_code = 405
    description = 'This resource does not support the specified HTTP method.'

    def __init__(self, allowed_methods: str, **kwargs):
        super().__init__(**kwargs)

        self.headers[hdrs.ALLOW] = allowed_methods


class ExpectationFailed(FailException):
    status_code = 417
    description = 'Unknown Expect: %s'

    def __init__(self, expect: str, **kwargs):
        self.description %= expect

        super().__init__(**kwargs)


class ErrorException(JsonException):
    status = 'error'


class InternalServerError(ErrorException):
    status_code = 500
    description = 'Server got itself in trouble.'
