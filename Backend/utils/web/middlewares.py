#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hmac
import base64
import asyncio
import traceback

import jwt
import asyncpg
from aiohttp import web
from aiohttp.web_request import Request

from .exceptions import (JsonException, InternalServerError, Forbidden,
                         InvalidAccess, ExpiredAccess, InvalidHeaderValue)
from .other import hash_host


async def error_middleware(app: web.Application, handler):
    async def middleware_handler(request: Request):
        def fatal():
            tb = traceback.format_exc()
            print(tb)
            return InternalServerError()

        try:
            resp = await handler(request)
        except (asyncio.CancelledError,
                asyncio.TimeoutError) as exc:
            raise exc
        except (web.HTTPException, JsonException) as exc:
            resp = exc
        except asyncpg.exceptions.RaiseError as exc:
            if exc.message == 'FORBIDDEN':
                resp = Forbidden()
            else:
                resp = fatal()
        except Exception:
            resp = fatal()

        return resp
    return middleware_handler


async def auth_middleware(app: web.Application, handler):
    async def middleware_handler(request: Request):
        auth = request.headers.get('Authorization', '').split(maxsplit=1)
        if auth:
            if auth[0] != 'Token':
                raise InvalidHeaderValue
            try:
                decoded = jwt.decode(
                    auth[1], key=app['cfg']['access_key']
                )
                host_digest = base64.b64decode(decoded['for'])
                if not hmac.compare_digest(host_digest, hash_host(request)):
                    raise InvalidAccess
                request.uid = decoded['id']
            except IndexError:
                raise InvalidHeaderValue
            except jwt.DecodeError:
                raise InvalidAccess
            except jwt.ExpiredSignatureError:
                raise ExpiredAccess
        else:
            request.uid = 0

        return await handler(request)
    return middleware_handler


async def database_middleware(app: web.Application, handler):
    async def middleware_handler(request: Request):
        request.conn = await app['db'].acquire()
        try:
            return await handler(request)
        finally:
            await app['db'].release(request.conn)
    return middleware_handler
