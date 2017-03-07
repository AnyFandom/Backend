#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from typing import Union

import asyncpg
from passlib.hash import pbkdf2_sha256

from .web.exceptions import UsernameAlreadyTaken


async def _pool_init(conn):
    # временный фикс для https://github.com/MagicStack/asyncpg/issues/82
    await conn.set_builtin_type_codec('citext', codec_name=25)
    # конец временного фикса


_sqls = {'users_get': "SELECT * FROM users",
         'users_add': "SELECT * FROM users_create ($1, $2)"}


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


async def get_users(conn: asyncpg.connection.Connection, *ids: str,
                    u: bool=False) -> list:
    if u and ids:
        resp = await conn.fetch(
            _sqls['users_get'] + ' WHERE username = ANY($1::citext[])', ids)
    elif ids:
        resp = await conn.fetch(
            _sqls['users_get'] + ' WHERE id = ANY($1::bigint[])',
            list(map(int, ids)))
    else:
        resp = await conn.fetch(_sqls['users_get'])

    return [dict(
        type='users',
        id=x['id'],
        attributes=dict(
            created_at=x['created_at'],
            edited_at=x['edited_at'],
            edited_by=x['edited_by'],
            username=x['username'],
            description=x['description']
        )
    ) for x in resp]

async def add_user(conn: asyncpg.connection.Connection,
                   username: str, password: str) -> int:
    try:
        return await conn.fetchval(_sqls['users_add'], username,
                                   pbkdf2_sha256.hash(password))
    except asyncpg.exceptions.UniqueViolationError as exc:
        if exc.constraint_name == 'user_statics_username_key':
            raise UsernameAlreadyTaken
