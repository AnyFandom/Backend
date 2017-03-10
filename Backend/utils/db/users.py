#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

import asyncpg

_sqls = {'get': "SELECT * FROM users",
         'patch': "SELECT * FROM users_update($1,$2,$3,$4)",
         'get_history': "SELECT * FROM users_history($1,$2)"}

async def get(conn: asyncpg.connection.Connection,
              *ids: Union[str, int], u: bool=False) -> list:
    if u and ids:
        resp = await conn.fetch(
            _sqls['get'] + ' WHERE username = ANY($1::citext[])', ids)
    elif ids:
        resp = await conn.fetch(
            _sqls['get'] + ' WHERE id = ANY($1::BIGINT[])',
            list(map(int, ids)))
    else:
        resp = await conn.fetch(_sqls['get'])

    return [dict(
        type='users',
        id=x['id'],
        attributes=dict(
            created_at=x['created_at'],
            edited_at=x['edited_at'],
            edited_by=x['edited_by'],
            username=x['username'],
            description=x['description'],
            avatar=x['avatar']
        )
    ) for x in resp]


async def patch(conn: asyncpg.connection.Connection,
                uid: int, id_: int, fields):
    if not fields:
        return

    await conn.execute(_sqls['patch'], id_, uid,
                       fields.get('description'), fields.get('avatar'))


async def get_history(conn: asyncpg.connection.Connection,
                      uid: int, id_: int):
    resp = await conn.fetch(_sqls['get_history'], id_, uid)

    return [dict(
        type='users',
        id=x['id'],
        attributes=dict(
            created_at=x['created_at'],
            edited_at=x['edited_at'],
            edited_by=x['edited_by'],
            username=x['username'],
            description=x['description'],
            avatar=x['avatar']
        )
    ) for x in resp]
