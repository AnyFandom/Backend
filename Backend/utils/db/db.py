#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

import asyncpg
import aiohttp.web_request


class DB:
    def __init__(self, pool: asyncpg.pool.Pool) -> None:
        self._pool = pool

    @classmethod
    async def init(cls, *, host: str=None, port: int=None, database: str=None,
                   user: str=None, password: str=None,
                   min_size: int, max_size: int,
                   loop: asyncio.AbstractEventLoop) -> 'DB':

        self = cls(await asyncpg.create_pool(
            host=host, port=port, user=user, password=password,
            database=database, min_size=min_size, max_size=max_size,
            loop=loop
        ))

        return self

    def acquire(self) -> asyncpg.pool.PoolAcquireContext:
        return self._pool.acquire()

    async def release(self, conn: asyncpg.connection.Connection):
        await self._pool.release(conn)

    async def close(self):
        await self._pool.close()


def postgres(func):
    async def wrapped(*args, **kwargs):
        if isinstance(args[0], aiohttp.web_request.Request):
            args[0].conn = await args[0].app['db'].acquire()

            try:
                return await func(*args, **kwargs)
            finally:
                await args[0].app['db'].release(args[0].conn)

        else:
            args[0].request.conn = await args[0].request.app['db'].acquire()

            try:
                return await func(*args, **kwargs)
            finally:
                await args[0].request.app['db'].release(args[0].request.conn)

    return wrapped
