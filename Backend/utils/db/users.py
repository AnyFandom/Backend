#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncpg

_sqls = {'get_users': "SELECT * FROM users",
         'patch_users': "SELECT * FROM users_update($1,$2,$3,$4)"}

async def get_users(conn: asyncpg.connection.Connection, *ids: str,
                    u: bool=False) -> list:
    if u and ids:
        resp = await conn.fetch(
            _sqls['get_users'] + ' WHERE username = ANY($1::citext[])', ids)
    elif ids:
        resp = await conn.fetch(
            _sqls['get_users'] + ' WHERE id = ANY($1::bigint[])',
            list(map(int, ids)))
    else:
        resp = await conn.fetch(_sqls['get_users'])

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


async def patch_users(conn: asyncpg.connection.Connection, uid: id,
                      id_: int, fields):
    if not fields:
        return

    await conn.execute(_sqls['patch_users'], uid, id_,
                       fields.get('description'), fields.get('avatar'))
