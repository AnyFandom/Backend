#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

import uvloop
from aiohttp import web

from .views import (auth, RootView,
                    UserView, UserListView, UserHistoryView,
                    FandomListView, FandomView)

from .utils import DB
from .utils.web import middlewares, Router


async def create_app(loop: asyncio.AbstractEventLoop,
                     config: dict) -> web.Application:
    app = web.Application(loop=loop, router=Router(), middlewares=[
        middlewares.error_middleware,
        middlewares.auth_middleware,
        middlewares.database_middleware
    ])

    url = app.router.add_route

    url('*', '/', RootView)

    url('POST', '/auth/register', auth.register)
    url('POST', '/auth/login', auth.login)
    url('POST', '/auth/refresh', auth.refresh)
    url('POST', '/auth/invalidate', auth.invalidate)
    url('POST', '/auth/change', auth.change)
    url('POST', '/auth/reset', auth.reset)

    url('*', '/users', UserListView)
    url('*', '/users/{first:(u)}/{second:\w+}', UserView)  # URL
    url('*', '/users/{first:(u)}/{second:\w+}/history', UserHistoryView)

    url('*', '/users/{first:\w+}', UserView)               # ID | CURRENT
    url('*', '/users/{first:\w+}/history', UserHistoryView)

    url('*', '/fandoms', FandomListView)
    url('*', '/fandoms/{first:(u)}/{second:\w+}', FandomView)

    url('*', '/fandoms/{first:\w+}', FandomView)

    app['cfg'] = config
    app['db'] = await DB.init(loop=loop, **config['db'])

    return app


def main(config: dict):
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app(loop, config))

    handler = app.make_handler()
    server = loop.run_until_complete(loop.create_server(
        handler, config['server']['host'], config['server']['port']))

    print('Server running at http://{}:{}/'.format(
        config['server']['host'], config['server']['port']))

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
