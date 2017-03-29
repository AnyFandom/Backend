#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

import uvloop
from aiohttp import web

from .views import (auth, RootView,
                    UserListView, UserView, UserHistoryView,
                    FandomListView, FandomView, FandomHistoryView)

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
    url('*', '/fandoms/{first:(u)}/{second:\w+}/history', FandomHistoryView)

    url('*', '/fandoms/{first:\w+}', FandomView)
    url('*', '/fandoms/{first:\w+}/history', FandomHistoryView)

    app['cfg'] = config
    app['db'] = await DB.init(
        loop=loop, host=config['db_host'], port=int(config['db_port']),
        database=config['db_database'], user=config['db_user'],
        password=config['db_password'], max_size=int(config['pool_max']),
        min_size=int(config['pool_min'])
    )

    return app


def main(config: dict):
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app(loop, config))

    handler = app.make_handler()
    server = loop.run_until_complete(loop.create_server(
        handler, config['server_host'], int(config['server_port'])))

    print('Server running at port {}'.format(config['server_port']))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print('Shutting down server at port {}'.format(config['server_port']))
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.run_until_complete(app['db'].close())
        loop.run_until_complete(handler.shutdown(60.0))

    loop.close()
