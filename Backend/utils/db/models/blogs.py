#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from .base import Obj
from ...web.exceptions import (Forbidden, ObjectNotFound, AlreadyModer,
                               AlreadyBanned, UserIsBanned, UserIsModer,
                               BlogUrlAlreadyTaken)
from .users import User
from .fandoms import FandomModer, FandomBanned

__all__ = ('Blog',)


class Blog(Obj):
    _sqls = dict(
        select="SELECT * FROM blogs %s ORDER BY id",

        # args: user_id, fandom_id, url, title, description, avatar
        insert="SELECT blogs_create($1, $2, $3, $4, $5, $6)",

        # args: edited_by, blog_id, title, description, avatar
        update="UPDATE blogs SET edited_by=$1, "
               "title=$3, description=$4, avatar=$5 WHERE id=$2",

        # args: blog_id
        delete="DELETE FROM blogs WHERE id=$1",

        # args: blog_id
        history="SELECT * FROM blogs_history($1) ORDER BY id, edited_at ASC",

        # args: user_id, blog_id
        check_owner="SELECT EXISTS (SELECT 1 FROM blogs "
                    "WHERE owner=$1 AND id=$2)"
    )

    _type = 'blogs'

    @classmethod
    async def check_owner(cls, conn: asyncpg.connection.Connection,
                          user_id: int, blog_id: int):
        """Использовать только в крайних случаях"""
        return await conn.fetchval(cls._sqls['check_owner'], user_id, blog_id)

    @classmethod
    async def id_u(cls, request) -> 'Blog':
        conn = request.conn
        blog = request.match_info['blog']
        uid = request.uid

        try:
            return (await cls.select(conn, 0, uid, blog))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    # noinspection PyMethodOverriding
    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, fandom_id: int,
                     user_id: int, *target_ids: Union[int, str],
                     u: bool=False) -> Tuple['Blog', ...]:

        # На вход поданы url
        if u and target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE url = ANY($1::CITEXT[]) "
                                      "AND fandom_id = $2",
                target_ids, fandom_id)

        # На вход поданы ID
        elif target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[])",
                tuple(map(int, target_ids)))

        # На вход не подано ничего
        else:
            resp = await conn.fetch(cls._sqls['select'] % '')

        return tuple(cls(x, conn, user_id) for x in resp)

    # noinspection PyMethodOverriding
    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, fandom_id: int,
                     user_id: int, fields: dict) -> int:

        # TODO: Больше проверок
        if (
            await FandomBanned.check_exists(conn, user_id, fandom_id)
        ):
            raise Forbidden

        try:
            return await conn.fetchval(
                cls._sqls['insert'], user_id, fandom_id, fields['url'],
                fields['title'], fields['description'], fields['avatar'])
        except asyncpg.exceptions.UniqueViolationError:
            raise BlogUrlAlreadyTaken

    async def update(self, fields: dict):

        # Проверка
        if (
            self.attrs['owner'] != self._uid and
            # TODO: BlogModer.check_exists
            not await FandomModer.check_exists(
                self._conn, self._uid, self.id, 'edit_b') and
            not await User.check_admin(self._conn, self._uid)
        ):
            return Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self.id,
            fields['title'], fields['description'], fields['avatar'])

    async def history(self) -> Tuple['Blog', ...]:

        # Проверка
        if (
            self.attrs['owner'] != self._uid and
            # TODO: BlogModer.check_exists
            not await FandomModer.check_exists(
                self._conn, self._uid,
                self.attrs['fandom_id'], 'edit_b') and
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self.id)

        return tuple(self.__class__(x) for x in resp)
