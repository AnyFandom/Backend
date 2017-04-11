#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid

import asyncpg
from passlib.hash import pbkdf2_sha256

from ..web.exceptions import UsernameAlreadyTaken, AuthFail

_sqls = dict(
    register="SELECT * FROM users_create ($1, $2)",
    login="SELECT * FROM auth WHERE username = $1::CITEXT",
    check_random="SELECT random = $1::UUID FROM auth WHERE id = $2",
    reset_random="UPDATE auth SET random = DEFAULT WHERE id = $1",
    change="UPDATE auth SET password_hash = $1 WHERE id = $2"
)


async def _reset_random(conn: asyncpg.connection.Connection, id_: int):
    await conn.execute(_sqls['reset_random'], id_)


async def register(conn: asyncpg.connection.Connection,
                   username: str, password: str) -> int:
    try:
        return await conn.fetchval(
            _sqls['register'], username, pbkdf2_sha256.hash(password))
    except asyncpg.exceptions.UniqueViolationError as exc:
        if exc.constraint_name == 'user_statics_username_key':
            raise UsernameAlreadyTaken


async def login(conn: asyncpg.connection.Connection,
                username: str, password: str) -> (int, str):
    data = await conn.fetchrow(_sqls['login'], username)

    if not data or not pbkdf2_sha256.verify(password, data['password_hash']):
        raise AuthFail

    return data['id'], data['random']


async def check_random(conn: asyncpg.connection.Connection,
                       id_: int, random: str) -> bool:
    return await conn.fetchval(
        _sqls['check_random'], uuid.UUID(bytes=random), id_)


async def invalidate(conn: asyncpg.connection.Connection,
                     username: str, password: str):
    id_, _ = await login(conn, username, password)

    await _reset_random(conn, id_)


async def change(conn: asyncpg.connection.Connection,
                 username: str, password: str, new_password: str):
    id_, _ = await login(conn, username, password)

    await _reset_random(conn, id_)
    await conn.execute(_sqls['change'], pbkdf2_sha256.hash(new_password), id_)
