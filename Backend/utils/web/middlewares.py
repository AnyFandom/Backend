#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

from aiohttp import web, errors

from .exceptions import JsonException, InternalServerError


async def error_middleware(app: web.Application, handler):
    async def middleware_handler(request):
        try:
            resp = await handler(request)
        except (asyncio.CancelledError,
                asyncio.TimeoutError,
                errors.ClientDisconnectedError) as exc:
            raise exc
        except (web.HTTPException, JsonException) as exc:
            resp = exc
        except Exception:
            resp = InternalServerError()

        return resp
    return middleware_handler
