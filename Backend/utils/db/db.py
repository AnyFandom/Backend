#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

import asyncpg


async def _pool_init(conn):
    # временный фикс для https://github.com/MagicStack/asyncpg/issues/82
    await conn.set_builtin_type_codec('citext', codec_name=25)
    # конец временного фикса


class DB:
    def __init__(self, pool: asyncpg.pool.Pool):
        self._pool = pool

    @classmethod
    async def init(cls, *, host: str=None, port: int=None, database: str=None,
                   user: str=None, password: str=None,
                   min_size: int, max_size: int,
                   loop: asyncio.AbstractEventLoop) -> 'DB':

        self = cls(await asyncpg.create_pool(
            host=host, port=port, user=user, password=password,
            database=database, min_size=min_size, max_size=max_size,
            loop=loop, init=_pool_init
        ))

        return self

    def acquire(self) -> asyncpg.pool.PoolAcquireContext:
        return self._pool.acquire()

    async def release(self, conn: asyncpg.connection.Connection):
        await self._pool.release(conn)

    async def close(self):
        await self._pool.close()


