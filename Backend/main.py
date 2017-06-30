#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

import uvloop
from aiohttp import web

from . import views
from .utils import DB
from .utils.web import middlewares, Router


async def create_app(loop: asyncio.AbstractEventLoop,
                     config: dict) -> web.Application:
    app = web.Application(loop=loop, router=Router(), middlewares=[
        middlewares.error_middleware,
        middlewares.auth_middleware,
        middlewares.database_middleware
    ])

    _arg = '(\w+)|(u\/\w+)'

    url = app.router.add_route

    url('*', '/', views.root.Root)

    url('POST', '/auth/register', views.register)
    url('POST', '/auth/login', views.login)
    url('POST', '/auth/refresh', views.refresh)
    url('POST', '/auth/invalidate', views.invalidate)
    url('POST', '/auth/change', views.change)
    url('POST', '/auth/reset', views.reset)

    url('*', '/users', views.UserList)
    url('*', '/users/{user:' + _arg + '}', views.User)
    url('*', '/users/{user:' + _arg + '}/history', views.UserHistory)

    url('*', '/fandoms', views.fandoms.FandomList)
    url('*', '/fandoms/{fandom:' + _arg + '}', views.Fandom)
    url('*', '/fandoms/{fandom:' + _arg + '}/history', views.FandomHistory)
    url('*', '/fandoms/{fandom:' + _arg + '}/moders', views.FandomModerList)
    url('*', '/fandoms/{fandom:' + _arg + '}/moders/{moder:\w+}',
        views.FandomModer)
    url('*', '/fandoms/{fandom:' + _arg + '}/bans', views.FandomBannedList)
    url('*', '/fandoms/{fandom:' + _arg + '}/bans/{banned:\w+}',
        views.FandomBanned)
    url('*', '/fandoms/{fandom:' + _arg + '}/blogs', views.FandomBlogList)
    url('*', '/fandoms/{fandom:' + _arg + '}/blogs/{blog:' + _arg + '}',
        views.FandomBlog)

    url('*', '/blogs', views.BlogList)
    url('*', '/blogs/{blog:\w+}', views.Blog)
    url('*', '/blogs/{blog:\w+}/history', views.BlogHistory)
    url('*', '/blogs/{blog:\w+}/moders', views.BlogModerList)
    url('*', '/blogs/{blog:\w+}/moders/{moder:\w+}', views.BlogModer)
    url('*', '/blogs/{blog:\w+}/bans', views.BlogBannedList)
    url('*', '/blogs/{blog:\w+}/bans/{banned:\w+}', views.BlogBanned)

    if bool(int(config['test'])):
        print('RUNNING IN TEST MODE')
        url('POST', '/clear_db', views.clear_db)
        url('POST', '/execute', views.execute)
        app.middlewares.insert(0, middlewares.timeit_middleware)

    config['access_key'] = config['access_key'].encode('utf-8')
    config['refresh_key'] = config['refresh_key'].encode('utf-8')

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
