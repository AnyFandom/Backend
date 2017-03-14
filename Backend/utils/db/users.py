#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

import asyncpg

_sqls = {'get': "SELECT * FROM users",
         'patch': "SELECT * FROM users_update($1,$2,$3,$4)",
         'get_history': "SELECT * FROM users_history($1,$2)"}


def _format(obj):
    return dict(
        type='users',
        id=obj['id'],
        attributes=dict(
            created_at=obj['created_at'],
            edited_at=obj['edited_at'],
            edited_by=obj['edited_by'],
            username=obj['username'],
            description=obj['description'],
            avatar=obj['avatar']
        )
    )

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

    return [_format(x) for x in resp]


async def patch(conn: asyncpg.connection.Connection,
                uid: int, id_: int, fields):
    if not fields:
        return

    await conn.execute(_sqls['patch'], id_, uid,
                       fields.get('description'), fields.get('avatar'))


async def get_history(conn: asyncpg.connection.Connection,
                      uid: int, id_: int):
    resp = await conn.fetch(_sqls['get_history'], id_, uid)

    return [_format(x) for x in resp]
