#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncpg

_sqls = {'get_users': "SELECT * FROM users"}

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
            description=x['description']
        )
    ) for x in resp]
