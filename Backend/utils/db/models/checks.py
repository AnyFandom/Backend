#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncpg

__all__ = ('user', 'admin',
           'fandom_moder', 'fandom_banned',
           'blog_moder', 'blog_banned', 'blog_owner')

_sqls = dict(
    user="SELECT EXISTS (SELECT 1 FROM users WHERE id=$1)",

    user_admin="SELECT EXISTS (SELECT 1 FROM admins WHERE user_id=$1)",

    fandom_moder="SELECT EXISTS (SELECT 1 FROM fandom_moders "
                 "WHERE user_id=$1 AND target_id=$2 %s)",

    fandom_banned="SELECT EXISTS (SELECT 1 FROM fandom_bans "
                  "WHERE user_id=$1 AND target_id=$2)",

    blog_moder="SELECT EXISTS (SELECT 1 FROM blog_moders "
               "WHERE user_id=$1 AND target_id=$2 %s)",

    blog_banned="SELECT EXISTS (SELECT 1 FROM blog_bans "
                "WHERE user_id=$1 AND blog_id=$2)",

    blog_owner="SELECT EXISTS (SELECT 1 FROM blogs "
               "WHERE owner=$1 AND id=$2)"
)


async def user(conn: asyncpg.connection.Connection, user_id: int) -> bool:
    return await conn.fetchval(_sqls['user'], user_id)

async def admin(conn: asyncpg.connection.Connection,
                     user_id: int) -> bool:

    return await conn.fetchval(_sqls['user_admin'], user_id)

async def fandom_moder(conn: asyncpg.connection.Connection, user_id: int,
                       fandom_id: int, perm: str=None) -> bool:

    return await conn.fetchval(
        _sqls['fandom_moder'] % ('AND %s=TRUE' % perm) if perm else '',
        user_id, fandom_id)

async def fandom_banned(conn: asyncpg.connection.Connection, user_id: int,
                        fandom_id: int) -> bool:

    return await conn.fetchval(_sqls['fandom_banned'], user_id, fandom_id)

async def blog_moder(conn: asyncpg.connection.Connection, user_id: int,
                     blog_id: int, perm: str=None) -> bool:

    return await conn.fetchval(
        _sqls['blog_moder'] % ('AND %s=TRUE' % perm) if perm else '',
        user_id, blog_id)

async def blog_banned(conn: asyncpg.connection.Connection, user_id: int,
                      blog_id: int) -> bool:

    return await conn.fetchval(_sqls['blog_banned'], user_id, blog_id)

async def blog_owner(conn: asyncpg.connection.Connection, user_id: int,
                     blog_id: int) -> bool:

    return await conn.fetchval(_sqls['blog_owner'], user_id, blog_id)
