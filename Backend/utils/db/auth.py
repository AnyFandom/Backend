#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
from typing import Tuple

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


async def _reset_random(conn: asyncpg.connection.Connection, user_id: int):
    await conn.execute(_sqls['reset_random'], user_id)


async def register(conn: asyncpg.connection.Connection,
                   username: str, password: str) -> int:
    try:
        return await conn.fetchval(
            _sqls['register'], username, pbkdf2_sha256.hash(password))
    except asyncpg.exceptions.UniqueViolationError:
        raise UsernameAlreadyTaken


async def login(conn: asyncpg.connection.Connection,
                username: str, password: str) -> Tuple[int, uuid.UUID]:
    data = await conn.fetchrow(_sqls['login'], username)

    if not data or not pbkdf2_sha256.verify(password, data['password_hash']):
        raise AuthFail

    return data['id'], data['random']


async def check_random(conn: asyncpg.connection.Connection,
                       user_id: int, random: bytes) -> bool:
    return await conn.fetchval(
        _sqls['check_random'], uuid.UUID(bytes=random), user_id)


async def invalidate(conn: asyncpg.connection.Connection,
                     username: str, password: str):
    user_id, _ = await login(conn, username, password)

    await _reset_random(conn, user_id)


async def change(conn: asyncpg.connection.Connection,
                 username: str, password: str, new_password: str):
    user_id, _ = await login(conn, username, password)

    await _reset_random(conn, user_id)
    await conn.execute(
        _sqls['change'], pbkdf2_sha256.hash(new_password), user_id)
