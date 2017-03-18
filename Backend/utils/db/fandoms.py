#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

import asyncpg

from ..web.exceptions import FandomUrlAlreadyTaken

_sqls = {'add': "SELECT fandoms_create($1, $2, $3, $4, $5)",
         'get': "SELECT * FROM fandoms"}


def _format(obj):
    return dict(
        type='fandoms',
        id=obj['id'],
        attributes=dict(
            created_at=obj['created_at'],
            edited_at=obj['edited_at'],
            edited_by=obj['edited_by'],
            title=obj['title'],
            url=obj['url'],
            description=obj['description'],
            avatar=obj['avatar'],
            owner=obj['owner']
        )
    )


async def add(conn: asyncpg.connection.Connection,
              uid: int, title: str, url: str, descr: str, avatar: str) -> int:
    try:
        return await conn.fetchval(
            _sqls['add'], uid, url, title, descr, avatar
        )
    except asyncpg.exceptions.UniqueViolationError as exc:
        if exc.constraint_name == 'fandom_statics_url_key':
            raise FandomUrlAlreadyTaken


async def get(conn: asyncpg.connection.Connection,
              *ids: Union[str, int], u: bool=False) -> list:
    if u and ids:
        resp = await conn.fetch(
            _sqls['get'] + " WHERE url = ANY($1::CITEXT[])", ids)
    elif ids:
        resp = await conn.fetch(
            _sqls['get'] + " WHERE id = ANY($1::BIGINT[])", ids)
    else:
        resp = await conn.fetch(_sqls['get'])

    return [_format(x) for x in resp]
