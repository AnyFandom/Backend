#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

import uvloop
from aiohttp import web

from .views import RootView
from .utils.db import DB
from .utils.web import middlewares


async def create_app(loop: asyncio.AbstractEventLoop) -> web.Application:
    app = web.Application(loop=loop, middlewares=[
        middlewares.error_middleware,
        middlewares.database_middleware
    ])

    app.router.add_route('*', '/', RootView)

    app['db'] = await DB.init(
        database='AnyFandom', min_size=10, max_size=10, loop=loop)

    return app


def main(host: str, port: int):
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app(loop))

    handler = app.make_handler()
    server = loop.run_until_complete(loop.create_server(handler, host, port))

    print('Server running at http://{}:{}/'.format(host, port))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print('Shutting down')
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.run_until_complete(app['db'].close())
        loop.run_until_complete(handler.shutdown(60.0))

    loop.close()
