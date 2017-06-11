#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import socket
import asyncio
import traceback

from aiohttp import web
from aiohttp.web_request import Request

from .tkn import decode_timed
from .exceptions import (JsonException, InternalServerError,
                         InvalidToken, InvalidHeaderValue)


async def timeit_middleware(app: web.Application, handler):
    async def middleware_handler(request: Request):
        start_time = time.time()
        resp = await handler(request)
        print(format(time.time() - start_time, '.15f'), ':', request.method,
              request.rel_url, '->', getattr(resp, 'status_code', resp.status))

        return resp
    return middleware_handler


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
                decoded = decode_timed(
                    auth[1].encode('utf-8'), key=app['cfg']['access_key'])

                host = decoded[1]
                if host != socket.inet_aton(request.headers['X-Real-IP']):
                    raise InvalidToken
                request.uid = decoded[0]
            except IndexError:
                raise InvalidHeaderValue
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
