#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from .base import Obj, SelectResult
from ...web.exceptions import (Forbidden, ObjectNotFound, UserIsBanned,
                               UserIsModer, UserIsOwner, BlogUrlAlreadyTaken)
from .users import User
from .fandoms import FandomModer, FandomBanned

__all__ = ('BlogModer', 'BlogBanned', 'Blog')


class BlogModer(Obj):
    _meta = ('blog_id', 'edit_b', 'manage_b', 'ban_b',
             'create_p', 'edit_p', 'edit_c')

    _sqls = dict(
        # args: blog_id
        select="SELECT u.*, bm.target_id AS blog_id, bm.edit_b, bm.manage_b,"
               "bm.ban_b, bm.create_p, fm.edit_p, fm.edit_c "
               "FROM blog_moders AS bm "
               "INNER JOIN users AS u ON bm.user_id=u.id "
               "WHERE bm.target_id=$1 %s ORDER BY u.id ASC",

        # args: user_id, blog_id, edit_b, manage_b, ban_b, create_p, edit_p,
        #       edit_c
        insert="INSERT INTO blog_moders (user_id, target_id, edit_b, "
               "manage_b, ban_b, create_p, edit_p, edit_c)"
               "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",

        # args: user_id, blog_id, edit_b, manage_b, ban_b, create_p, edit_p,
        #       edit_c
        update="UPDATE blog_moders SET target_id=$2, edit_b=$3, "
               "manage_b=$4, ban_b=$5, create_p=$6, edit_p=$7, edit_c=$8 "
               "WHERE user_id=$1",

        # args: user_id, blog_id
        delete="DELETE FROM blog_moders WHERE user_id=$1 AND target_id=$2",

        # args: user_id, blog_id
        check_exists="SELECT EXISTS (SELECT 1 FROM blog_moders "
                     "WHERE user_id=$1 AND target_id=$2 %s)"
    )

    _type = 'users'

    @classmethod
    async def check_exists(cls, conn: asyncpg.connection.Connection,
                           user_id: int, blog_id: int,
                           perm: str=None) -> bool:

        return await conn.fetchval(
            cls._sqls['check_exists'] % ('AND %s=TRUE' % perm) if perm else '',
            user_id, blog_id)

    # noinspection PyMethodOverriding
    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     blog_id: int, *target_ids: Union[int, str]
                     ) -> Tuple['BlogModer', ...]:

        # На вход поданы ID
        if target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % 'AND bm.user_id = ANY($2::BIGINT[])',
                blog_id, tuple(map(int, target_ids)))

        # На вход не подано ничего
        else:
            resp = await conn.fetch(cls._sqls['select'] % '', blog_id)

        return SelectResult(cls(x, conn, user_id, cls._meta) for x in resp)

    # noinspection PyMethodOverriding
    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, blog_id: int, fields: dict):

        # Проверка
        if (
            not await Blog.check_owner(
                conn, user_id, blog_id) and
            not await BlogModer.check_exists(
                conn, user_id, blog_id, 'manage_b') and
            not await User.check_admin(
                conn, user_id)
        ):
            raise Forbidden

        # Существует ли юзер
        if not await User.check_exists(conn, fields['user_id']):
            raise ObjectNotFound

        # А не овнер ли он?
        if await Blog.check_owner(conn, fields['user_id'], blog_id):
            raise UserIsOwner('moder', 'blog')

        # А не забанен ли он?
        if await BlogBanned.check_exists(conn, fields['user_id'], blog_id):
            raise UserIsBanned('moder', 'blog')
        if await FandomBanned.check_exists(conn, fields['user_id'], fandom_id):
            raise UserIsBanned('moder', 'fandom')

        try:
            await conn.execute(
                cls._sqls['insert'], fields['user_id'], user_id,
                fields['edit_b'], fields['manage_b'], fields['ban_b'],
                fields['create_p'], fields['edit_p'], fields['edit_c']
            )
        except asyncpg.exceptions.UniqueViolationError:
            raise UserIsModer('moder', 'blog')

    async def update(self, fields: dict):

        # Проверка
        if (
            not await Blog.check_owner(
                self._conn, self._uid, self.id) and
            not await BlogModer.check_exists(
                self._conn, self._uid, self.meta['blog_id'], 'manage_b') and
            not await User.check_admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self.id,
            self.meta['fandom_id'],
            fields['edit_f'], fields['manage_f'], fields['ban_f'],
            fields['create_b'], fields['edit_b'],
            fields['edit_p'], fields['edit_c'])

    async def delete(self):

        # Проверка
        if (
            not await Blog.check_owner(
                self._conn, self._uid, self.meta['blog_id']) and
            not await BlogModer.check_exists(
                self._conn, self._uid, self.meta['blog_id'], 'manage_f') and
            not await User.check_admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['delete'],

            self.id, self.meta['fandom_id']
        )


class BlogBanned(Obj):
    _meta = ('blog_id', 'set_by', 'reason')

    _sqls = dict(
        # args: blog_id
        select="SELECT u.*, bb.target_id as blog_id, bb.set_by, bb.reason "
               "FROM blog_bans as bb "
               "INNER JOIN users AS u ON bb.user_id=u.id "
               "WHERE bb.target_id=$1 %s ORDER BY u.id ASC",

        # args: user_id, blog_id, set_by, reason
        insert="INSERT INTO blog_bans (user_id, target_id, set_by, reason) "
               "VALUES ($1, $2, $3, $4)",

        # args: user_id, blog_id
        delete="DELETE FROM blog_bans WHERE user_id=$1 AND target_id=$2",

        # args: user_id, blog_id
        check_exists="SELECT EXISTS (SELECT 1 FROM blog_bans "
                     "WHERE user_id=$1 AND blog_id=$2)"
    )

    _type = 'users'

    @classmethod
    async def check_exists(cls, conn: asyncpg.connection.Connection,
                           user_id: int, blog_id: int) -> bool:

        return await conn.fetchval(
            cls._sqls['check_exists'], user_id, blog_id)

    # noinspection PyMethodOverriding
    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     blog_id: int, *target_ids: Union[int, str]):

        # На вход поданы ID
        if target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % 'AND bb.user_id = ANY($2::BIGINT[])',
                blog_id, tuple(map(int, target_ids)))

        # На вход не подано ничего
        else:
            resp = await conn.fetch(cls._sqls['select'] % '', blog_id)

        return SelectResult(cls(x, conn, user_id, cls._meta) for x in resp)

    # noinspection PyMethodOverriding
    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, blog_id: int, fields: dict):

        # Проверка
        if (
            not await Blog.check_owner(
                conn, user_id, blog_id) and
            not await BlogModer.check_exists(
                conn, user_id, blog_id, 'manage_b') and
            not await User.check_admin(
                conn, user_id)
        ):
            raise Forbidden

        # Существует ли юзер
        if not await User.check_exists(conn, fields['user_id']):
            raise ObjectNotFound

        # А не модер ли он?
        if await BlogModer.check_exists(conn, fields['user_id'], blog_id):
            raise UserIsModer('ban', 'blog')
        if await FandomModer.check_exists(conn, fields['user_id'], fandom_id):
            raise UserIsModer('ban', 'fandom')

        try:
            await conn.execute(
                cls._sqls['insert'],

                fields['user_id'], blog_id,
                user_id, fields['reason'])
        except asyncpg.exceptions.UniqueViolationError:
            raise UserIsBanned('ban', 'blog')

    async def update(self, fields):
        pass

    async def delete(self):

        # Проверка
        if (
            not await Blog.check_owner(
                self._conn, self._uid, self.meta['blog_id']) and
            not await BlogModer.check_exists(
                self._conn, self._uid, self.meta['blog_id']) and
            not await User.check_admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['delete'],

            self.id, self.meta['blog_id']
        )


class Blog(Obj):
    _sqls = dict(
        select="SELECT * FROM blogs %s ORDER BY id ASC",

        # args: user_id, fandom_id, url, title, description, avatar
        insert="SELECT blogs_create($1, $2, $3, $4, $5, $6)",

        # args: edited_by, blog_id, title, description, avatar
        update="UPDATE blogs SET edited_by=$1, "
               "title=$3, description=$4, avatar=$5 WHERE id=$2",

        # args: blog_id
        delete="DELETE FROM blogs WHERE id=$1",

        # args: blog_id
        history="SELECT * FROM blogs_history($1) ORDER BY edited_at DESC",

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
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, *target_ids: Union[int, str],
                     u: bool=False) -> Tuple['Blog', ...]:

        # На вход поданы url И fandom_id
        if u and target_ids and fandom_id:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE url = ANY($1::CITEXT[]) "
                                      "AND fandom_id = $2",
                target_ids, fandom_id)

        # На вход поданы ID И fandom_id
        elif target_ids and fandom_id:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[]) "
                                      "AND fandom_id = $2",
                tuple(map(int, target_ids)), fandom_id)

        # На вход поданы ID
        elif target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[])",
                tuple(map(int, target_ids)))

        # На вход не подано ничего
        else:
            resp = await conn.fetch(cls._sqls['select'] % '')

        return SelectResult(cls(x, conn, user_id) for x in resp)

    # noinspection PyMethodOverriding
    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, fields: dict) -> int:

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
            not await BlogModer.check_exists(
                self._conn, self._uid, self.id, 'edit_b') and
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
            not await BlogModer.check_exists(
                self._conn, self._uid, self.id, 'edit_b') and
            not await FandomModer.check_exists(
                self._conn, self._uid,
                self.attrs['fandom_id'], 'edit_b') and
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self.id)

        return SelectResult(self.__class__(x) for x in resp)

    # Moders

    async def moders_id_u(self, request) -> BlogModer:
        moder = request.match_info['moder']

        try:
            return (await self.moders_select(moder))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    async def moders_select(self, *target_ids: Union[int, str]
                            ) -> Tuple[BlogModer, ...]:

        return await BlogModer.select(
            self._conn, self._uid, self.id, *target_ids)

    async def moders_insert(self, fields: dict) -> Tuple[int, int]:

        await BlogModer.insert(
            self._conn, self._uid, self.id, self.attrs['fandom_id'], fields)

        return self.id, fields['user_id']

    # Bans

    async def bans_id_u(self, request) -> BlogBanned:
        banned = request.match_info['banned']

        try:
            return (await self.bans_select(banned))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    async def bans_select(self, *target_ids: Union[int, str]
                          ) -> Tuple[BlogBanned, ...]:

        return await BlogBanned.select(
            self._conn, self._uid, self.id, *target_ids)

    async def bans_insert(self, fields: dict) -> Tuple[int, int]:

        await BlogBanned.insert(
            self._conn, self._uid, self.id, self.attrs['fandom_id'], fields)

        return self.id, fields['user_id']
