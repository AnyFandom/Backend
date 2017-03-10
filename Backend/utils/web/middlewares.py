#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import traceback

import jwt
from aiohttp import web, errors, web_reqrep

from .exceptions import (JsonException, InternalServerError,
                         InvalidAccess, ExpiredAccess, InvalidHeaderValue)


async def error_middleware(app: web.Application, handler):
    async def middleware_handler(request: web_reqrep.Request):
        try:
            resp = await handler(request)
        except (asyncio.CancelledError,
                asyncio.TimeoutError,
                errors.ClientDisconnectedError) as exc:
            raise exc
        except (web.HTTPException, JsonException) as exc:
            resp = exc
        except Exception:
            tb = traceback.format_exc()
            print(tb)
            resp = InternalServerError()

        return resp
    return middleware_handler


async def auth_middleware(app: web.Application, handler):
    async def middleware_handler(request: web_reqrep.Request):
        auth = request.headers.get('Authorization', '').split(maxsplit=1)
        if auth:
            if auth[0] != 'Token':
                raise InvalidHeaderValue
            try:
                request.uid = jwt.decode(
                    auth[1], key=app['cfg']['jwt_key']
                )['id']
            except IndexError:
                raise InvalidHeaderValue
            except jwt.DecodeError:
                raise InvalidAccess
            except jwt.ExpiredSignatureError:
                raise ExpiredAccess
        else:
            request.uid = None

        return await handler(request)
    return middleware_handler


async def database_middleware(app: web.Application, handler):
    async def middleware_handler(request: web_reqrep.Request):
        request.conn = await app['db'].acquire()
        try:
            return await handler(request)
        finally:
            await app['db'].release(request.conn)
    return middleware_handler
