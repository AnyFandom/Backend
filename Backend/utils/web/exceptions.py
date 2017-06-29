#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import hdrs

from .rewrites import JsonResponse


class JsonException(JsonResponse, Exception):
    status: str = None
    status_code: int = None
    description: str = None

    def __init__(self, *, headers=None, reason=None, details=None):
        body = {'code': type(self).__name__, 'description': self.description}

        if details:
            body['details'] = details

        JsonResponse.__init__(self, body=body, status=self.status,
                              headers=headers, reason=reason,
                              status_code=self.status_code)
        Exception.__init__(self)


class FailException(JsonException):
    status = 'fail'


class ValidationError(FailException):
    status_code = 400
    description = 'One or multiple required parameters were not ' \
                  'transferred or invalid. See "details" for details.'


class AuthFail(FailException):
    status_code = 400
    description = 'Incorrect username or password.'


class InvalidToken(FailException):
    status_code = 400
    description = 'The specified token is invalid.'


class ExpiredToken(FailException):
    status_code = 400
    description = 'The specified token is expired.'


class InvalidHeaderValue(FailException):
    status_code = 400
    description = 'The value provided for one of the ' \
                  'HTTP headers was not in the correct format.'


class Forbidden(FailException):
    status_code = 403
    description = 'You do not have sufficient ' \
                  'permissions to perform this operation.'


class ResourceNotFound(FailException):
    status_code = 404
    description = 'The specified resource does not exists.'


class ObjectNotFound(FailException):
    status_code = 404
    description = 'Object with specified ID or username/url does not exists.'


class MethodNotAllowed(FailException):
    status_code = 405
    description = 'This resource does not support the specified HTTP method.'

    def __init__(self, allowed_methods: set, **kwargs) -> None:
        super().__init__(**kwargs)

        self.headers[hdrs.ALLOW] = ', '.join(sorted(allowed_methods))


class UsernameAlreadyTaken(FailException):
    status_code = 409
    description = 'This username is already taken.'


class FandomUrlAlreadyTaken(FailException):
    status_code = 409
    description = 'Fandom with specified url already exists.'


class BlogUrlAlreadyTaken(FailException):
    status_code = 409
    description = 'Blog with specified url already exists in this fandom.'


class UserIsModer(FailException):
    status_code = 409
    description = 'User that you are trying to %s is %smoderator of this %s'

    def __init__(self, action: str, place: str, **kwargs):
        assert action in ('moder', 'ban'), 'Invalid action'

        self.description %= (
            'add as moderator' if action == 'moder' else 'ban',
            'already ' if action == 'moder' else '', place)

        super().__init__(**kwargs)


class UserIsBanned(FailException):
    status_code = 409
    description = 'User that you are trying to %s is %sbanned from this %s'

    def __init__(self, action: str, place: str, **kwargs):
        assert action in ('moder', 'ban'), 'Invalid action'

        self.description %= (
            'add as moderator' if action == 'moder' else 'ban',
            'already ' if action == 'ban' else '', place)

        super().__init__(**kwargs)


class UserIsOwner(FailException):
    status_code = 409
    description = 'User that you are trying to %s is owner of this %s'

    def __init__(self, action: str, place: str, **kwargs):
        assert action in ('moder', 'ban'), 'Invalid action'

        self.description %= (
            'add as moderator' if action == 'moder' else 'ban', place)

        super().__init__(**kwargs)


class ExpectationFailed(FailException):
    status_code = 417
    description = 'Unknown Expect: %s'

    def __init__(self, expect: str, **kwargs) -> None:
        self.description %= expect

        super().__init__(**kwargs)


class InvalidJson(FailException):
    status_code = 422
    description = 'There is no JSON in the body of the request or it is ' \
                  'invalid. See "details" for details.'


class ErrorException(JsonException):
    status = 'error'


class InternalServerError(ErrorException):
    status_code = 500
    description = 'Server got itself in trouble.'


class NotYetImplemented(ErrorException):
    status_code = 501
    description = 'Soon™.'
