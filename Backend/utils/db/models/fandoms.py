#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from . import checks as C
from .base import Obj, SelectResult
from ...web.exceptions import (Forbidden, ObjectNotFound, UserIsBanned,
                               UserIsModer, FandomUrlAlreadyTaken)
from .blogs import Blog
from .posts import Post

__all__ = ('FandomModer', 'FandomBanned', 'Fandom')


class FandomModer(Obj):
    _meta = ('fandom_id', 'edit_f', 'manage_f', 'ban_f',
             'create_b', 'edit_b', 'edit_p', 'edit_c')

    _sqls = dict(
        # args: fandom_id
        select="SELECT u.*, fm.target_id AS fandom_id, fm.edit_f, fm.manage_f,"
               "fm.ban_f, fm.create_b, fm.edit_b, fm.edit_p, fm.edit_c "
               "FROM fandom_moders AS fm "
               "INNER JOIN users AS u ON fm.user_id=u.id "
               "WHERE fm.target_id=$1 %s ORDER BY u.id ASC",

        # args: user_id, fandom_id, edit_f, manage_f, ban_f, create_b, edit_b,
        #       edit_p, edit_c
        insert="INSERT INTO fandom_moders (user_id, target_id, edit_f, "
               "manage_f, ban_f, create_b, edit_b, edit_p, edit_c)"
               "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",

        # args: user_id, fandom_id, edit_f, manage_F, ban_f, create_b, edit_b,
        #       edit_p, edit_c
        update="UPDATE fandom_moders SET edit_f=$3, "
               "manage_f=$4, ban_f=$5, create_b=$6, edit_b=$7, edit_p=$8, "
               "edit_c=$9 WHERE user_id=$1 AND target_id=$2",

        # args: user_id, fandom_id
        delete="DELETE FROM fandom_moders WHERE user_id=$1 AND target_id=$2",
    )

    _type = 'users'

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, *target_ids: Union[int, str]
                     ) -> Tuple['FandomModer', ...]:

        # Ищем по ID
        if target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % 'AND fm.user_id = ANY($2::BIGINT[])',
                fandom_id, tuple(map(int, target_ids)))

        # Возвращаем все
        else:
            resp = await conn.fetch(cls._sqls['select'] % '', fandom_id)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, fields: dict):

        # Проверка
        if (
            not await C.fandom_moder(
                conn, user_id, fandom_id, 'manage_f') and
            not await C.admin(
                conn, user_id)
        ):
            raise Forbidden

        # Существует ли юзер
        if not await C.user(conn, fields['user_id']):
            raise ObjectNotFound

        # А не забанен ли он?
        if await C.fandom_banned(conn, fields['user_id'], fandom_id):
            raise UserIsBanned('moder', 'fandom')

        try:
            await conn.execute(
                cls._sqls['insert'],

                fields['user_id'], user_id,
                fields['edit_f'], fields['manage_f'], fields['ban_f'],
                fields['create_b'], fields['edit_b'],
                fields['edit_p'], fields['edit_c']
            )
        except asyncpg.exceptions.UniqueViolationError:
            raise UserIsModer('moder', 'fandom')

    async def update(self, fields: dict):

        # Проверка
        if (
            not await C.fandom_moder(
                self._conn, self._uid, self.meta['fandom_id'], 'manage_f') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self.id, self.meta['fandom_id'],
            fields['edit_f'], fields['manage_f'], fields['ban_f'],
            fields['create_b'], fields['edit_b'],
            fields['edit_p'], fields['edit_c'])

    async def delete(self):

        # Проверка
        if (
            not await C.fandom_moder(
                self._conn, self._uid, self.meta['fandom_id'], 'manage_f') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['delete'],

            self.id, self.meta['fandom_id']
        )


class FandomBanned(Obj):
    _meta = ('fandom_id', 'set_by', 'reason')

    _sqls = dict(
        # args: fandom_id
        select="SELECT u.*, fb.target_id as fandom_id, fb.set_by, fb.reason "
               "FROM fandom_bans AS fb "
               "INNER JOIN users AS u ON fb.user_id=u.id "
               "WHERE fb.target_id=$1 %s ORDER BY u.id ASC",

        # args: user_id, fandom_id, set_by, reason
        insert="INSERT INTO fandom_bans (user_id, target_id, set_by, reason) "
               "VALUES ($1, $2, $3, $4)",

        # args: user_id, fandom_id
        delete="DELETE FROM fandom_bans WHERE user_id=$1 AND target_id=$2",
    )

    _type = 'users'

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, *target_ids: Union[int, str]
                     ) -> Tuple['FandomBanned', ...]:

        # Ищем по ID
        if target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % 'AND fb.user_id = ANY($2::BIGINT[])',
                fandom_id, tuple(map(int, target_ids)))

        # Возвращаем все
        else:
            resp = await conn.fetch(cls._sqls['select'] % '', fandom_id)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, fields: dict):

        # Проверка
        if (
            not await C.fandom_moder(
                conn, user_id, fandom_id, 'ban_f') and
            not await C.admin(
                conn, user_id)
        ):
            raise Forbidden

        # Существует ли юзер
        if not await C.user(conn, fields['user_id']):
            raise ObjectNotFound

        # А не модер ли он?
        if await C.fandom_moder(conn, fields['user_id'], fandom_id):
            raise UserIsModer('ban', 'fandom')

        try:
            await conn.execute(
                cls._sqls['insert'],

                fields['user_id'], fandom_id,
                user_id, fields['reason'])
        except asyncpg.exceptions.UniqueViolationError:
            raise UserIsBanned('ban', 'fandom')

    async def update(self, fields):
        pass

    async def delete(self):

        # Проверка
        if (
            not await C.fandom_moder(
                self._conn, self._uid, self.meta['fandom_id'], 'ban_f') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['delete'],

            self.id, self.meta['fandom_id']
        )


class Fandom(Obj):
    _sqls = dict(
        select="SELECT * FROM fandoms %s ORDER BY id ASC",

        # args: user_id, url, title, description, avatar
        insert="SELECT fandoms_create($1, $2, $3, $4, $5)",

        # args: edited_by, fandom_id, title, description, avatar
        update="UPDATE fandoms SET edited_by=$1,"
               "title=$3, description=$4, avatar=$5 WHERE id=$2",

        # args: fandom_id
        history="SELECT * FROM fandoms_history($1) ORDER BY edited_at DESC"
    )

    _type = 'fandoms'

    @classmethod
    async def id_u(cls, request) -> 'Fandom':
        conn = request.conn
        fandom = request.match_info['fandom']
        uid = request.uid

        try:
            if fandom[:2] == 'u/':
                return (await cls.select(conn, uid, fandom[2:], u=True))[0]
            else:
                return (await cls.select(conn, uid, fandom))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection,
                     user_id: int, *target_ids: Union[int, str],
                     u: bool=False) -> Tuple['Fandom', ...]:

        # Ищем по url
        if u and target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE url = ANY($1::CITEXT[])",
                target_ids)

        # Ищем по ID
        elif target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[])",
                tuple(map(int, target_ids)))

        # Возвращаем все
        else:
            resp = await conn.fetch(cls._sqls['select'] % '')

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection,
                     user_id: int, fields: dict) -> int:

        # Проверка
        if not await C.admin(conn, user_id):
            raise Forbidden

        try:
            return await conn.fetchval(
                cls._sqls['insert'], user_id, fields['url'],
                fields['title'], fields['description'],
                fields['avatar'])
        except asyncpg.exceptions.UniqueViolationError:
            raise FandomUrlAlreadyTaken

    async def update(self, fields: dict):

        # Проверка
        if (
            not await C.fandom_moder(
                self._conn, self._uid, self.id, 'edit_f') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self.id,
            fields['title'], fields['description'], fields['avatar'])

    async def history(self) -> Tuple['Fandom', ...]:

        # Проверка
        if (
            not await C.fandom_moder(
                self._conn, self._uid, self.id, 'edit_f') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self.id)

        return SelectResult(self.__class__(x) for x in resp)

    # Moders

    async def moders_id_u(self, request) -> FandomModer:
        moder = request.match_info['moder']

        try:
            return (await self.moders_select(moder))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    async def moders_select(self, *target_ids: Union[int, str]
                            ) -> Tuple[FandomModer, ...]:

        return await FandomModer.select(
            self._conn, self._uid, self.id, *target_ids)

    async def moders_insert(self, fields: dict) -> Tuple[int, int]:

        await FandomModer.insert(
            self._conn, self._uid, self.id, fields)

        return self.id, fields['user_id']

    # Bans

    async def bans_id_u(self, request) -> FandomBanned:
        banned = request.match_info['banned']

        try:
            return (await self.bans_select(banned))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    async def bans_select(self, *target_ids: Union[int, str]
                          ) -> Tuple[FandomBanned, ...]:

        return await FandomBanned.select(
            self._conn, self._uid, self.id, *target_ids)

    async def bans_insert(self, fields: dict) -> Tuple[int, int]:

        await FandomBanned.insert(
            self._conn, self._uid, self.id, fields)

        return self.id, fields['user_id']

    # Blogs

    async def blogs_id_u(self, request) -> Blog:
        blog = request.match_info['blog']

        try:
            if blog[:2] == 'u/':
                return (await self.blogs_select(blog[2:], u=True))[0]
            else:
                return (await self.blogs_select(blog))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    async def blogs_select(self, *target_ids: Union[int, str], u: bool=False
                           ) -> Tuple['Blog', ...]:

        return await Blog.select(
            self._conn, self.id, self._uid, *target_ids, u=u)

    async def blogs_insert(self, fields: dict) -> int:

        return await Blog.insert(
            self._conn, self.id, self._uid, fields)

    # Posts

    async def posts_select(self, *target_ids: Union[int, str]
                           ) -> Tuple[Post, ...]:

        return await Post.select(
            self._conn, self._uid, 0, self.id, *target_ids)

