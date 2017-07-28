#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
from typing import Tuple

import asyncpg
from passlib.hash import pbkdf2_sha256

from ..web.exceptions import UsernameAlreadyTaken, AuthFail
from .models.base import Commands

_c = Commands(
    # args: username, password_hash
    register="SELECT * FROM users_create ($1, $2)",

    # args: username
    login="SELECT * FROM auth WHERE username = $1::CITEXT",

    # args: user_id, random
    check_random="SELECT random = $2::UUID FROM auth WHERE id = $1",

    # args: user_id
    reset_random="UPDATE auth SET random = DEFAULT WHERE id = $1",

    # args: user_id, password_hash
    change="UPDATE auth SET password_hash = $2 WHERE id = $1"
)


async def _reset_random(conn: asyncpg.connection.Connection, user_id: int):
    await _c.e.reset_random(conn, user_id)


async def register(conn: asyncpg.connection.Connection,
                   username: str, password: str) -> int:
    try:
        return await _c.v.register(
            conn, username, pbkdf2_sha256.hash(password))
    except asyncpg.exceptions.UniqueViolationError:
        raise UsernameAlreadyTaken


async def login(conn: asyncpg.connection.Connection,
                username: str, password: str) -> Tuple[int, uuid.UUID]:
    data = await _c.r.login(conn, username)

    if not data or not pbkdf2_sha256.verify(password, data['password_hash']):
        raise AuthFail

    return data['id'], data['random']


async def check_random(conn: asyncpg.connection.Connection,
                       user_id: int, random: bytes) -> bool:

    return await _c.v.check_random(conn, user_id, uuid.UUID(bytes=random))


async def invalidate(conn: asyncpg.connection.Connection,
                     username: str, password: str):
    user_id, _ = await login(conn, username, password)

    await _reset_random(conn, user_id)


async def change(conn: asyncpg.connection.Connection,
                 username: str, password: str, new_password: str):
    user_id, _ = await login(conn, username, password)

    await _reset_random(conn, user_id)
    await _c.e.change(conn, user_id, pbkdf2_sha256.hash(new_password))
