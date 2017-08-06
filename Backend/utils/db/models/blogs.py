#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from . import checks as C
from .base import Obj, SelectResult, Commands
from ...web.exceptions import (Forbidden, ObjectNotFound, UserIsBanned,
                               UserIsModer, UserIsOwner, BlogUrlAlreadyTaken)
from .posts import Post

__all__ = ('BlogModer', 'BlogBanned', 'Blog')


class BlogModer(Obj):
    _meta = ('blog_id', 'edit_b', 'manage_b', 'ban_b',
             'create_p', 'edit_p', 'edit_c')

    _c = Commands(
        # args: blog_id
        select="SELECT u.*, bm.target_id AS blog_id, bm.edit_b, bm.manage_b,"
               "bm.ban_b, bm.create_p, bm.edit_p, bm.edit_c "
               "FROM blog_moders AS bm "
               "INNER JOIN users AS u ON bm.user_id=u.id "
               "WHERE bm.target_id=$1 ORDER BY u.id ASC",

        # args: blog_id, user_ids
        select_by_id="SELECT u.*, bm.target_id AS blog_id, bm.edit_b, "
                     "bm.manage_b, bm.ban_b, bm.create_p, bm.edit_p, "
                     "bm.edit_c "
                     "FROM blog_moders AS bm "
                     "INNER JOIN users AS u ON bm.user_id=u.id "
                     "WHERE bm.target_id=$1 "
                     "AND bm.user_id = ANY($2::BIGINT[]) ORDER BY u.id ASC",

        # args: user_id, blog_id, edit_b, manage_b, ban_b, create_p, edit_p,
        #       edit_c
        insert="INSERT INTO blog_moders (user_id, target_id, edit_b, "
               "manage_b, ban_b, create_p, edit_p, edit_c)"
               "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",

        # args: user_id, blog_id, edit_b, manage_b, ban_b, create_p, edit_p,
        #       edit_c
        update="UPDATE blog_moders SET edit_b=$3, "
               "manage_b=$4, ban_b=$5, create_p=$6, edit_p=$7, edit_c=$8 "
               "WHERE user_id=$1 AND target_id=$2",

        # args: user_id, blog_id
        delete="DELETE FROM blog_moders WHERE user_id=$1 AND target_id=$2",
    )

    _type = 'users'

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     blog_id: int, *target_ids: Union[int, str]
                     ) -> Tuple['BlogModer', ...]:

        # Ищем по ID
        if target_ids:
            resp = await cls._c.select_by_id(
                conn, blog_id, tuple(map(int, target_ids)))

        # Возвращаем все
        else:
            resp = await cls._c.select(conn, blog_id)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, blog_id: int, fields: dict):

        # Проверка
        if (
            not await C.blog_owner(
                conn, user_id, blog_id) and
            not await C.blog_moder(
                conn, user_id, blog_id, 'manage_b') and
            not await C.admin(
                conn, user_id)
        ):
            raise Forbidden

        # Существует ли юзер
        if not await C.user(conn, fields['user_id']):
            raise ObjectNotFound

        # А не овнер ли он?
        if await C.blog_owner(conn, fields['user_id'], blog_id):
            raise UserIsOwner('moder', 'blog')

        # А не забанен ли он?
        if await C.blog_banned(conn, fields['user_id'], blog_id):
            raise UserIsBanned('moder', 'blog')
        if await C.fandom_banned(conn, fields['user_id'], fandom_id):
            raise UserIsBanned('moder', 'fandom')

        try:
            await cls._c.e.insert(
                conn, fields['user_id'], user_id,
                fields['edit_b'], fields['manage_b'], fields['ban_b'],
                fields['create_p'], fields['edit_p'], fields['edit_c'])
        except asyncpg.exceptions.UniqueViolationError:
            raise UserIsModer('moder', 'blog')

    async def update(self, fields: dict):

        # Проверка
        if (
            not await C.blog_owner(
                self._conn, self._uid, self.id) and
            not await C.blog_moder(
                self._conn, self._uid, self.meta['blog_id'], 'manage_b') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._c.e.update(
            self._conn, self.id, self.meta['fandom_id'],
            fields['edit_f'], fields['manage_f'], fields['ban_f'],
            fields['create_b'], fields['edit_b'],
            fields['edit_p'], fields['edit_c'])

    async def delete(self):

        # Проверка
        if (
            not await C.blog_owner(
                self._conn, self._uid, self.meta['blog_id']) and
            not await C.blog_moder(
                self._conn, self._uid, self.meta['blog_id'], 'manage_f') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._c.e.delete(self._conn, self.id, self.meta['fandom_id'])


class BlogBanned(Obj):
    _meta = ('blog_id', 'set_by', 'reason')

    _c = Commands(
        # args: blog_id
        select="SELECT u.*, bb.target_id as blog_id, bb.set_by, bb.reason "
               "FROM blog_bans as bb "
               "INNER JOIN users AS u ON bb.user_id=u.id "
               "WHERE bb.target_id=$1 ORDER BY u.id ASC",

        # args: blog_id, user_ids
        select_by_id="SELECT u.*, bb.target_id as blog_id, bb.set_by, "
                     "bb.reason "
                     "FROM blog_bans as bb "
                     "INNER JOIN users AS u ON bb.user_id=u.id "
                     "WHERE bb.target_id=$1 "
                     "AND bb.user_id = ANY($2::BIGINT[]) ORDER BY u.id ASC",

        # args: user_id, blog_id, set_by, reason
        insert="INSERT INTO blog_bans (user_id, target_id, set_by, reason) "
               "VALUES ($1, $2, $3, $4)",

        # args: user_id, blog_id
        delete="DELETE FROM blog_bans WHERE user_id=$1 AND target_id=$2",
    )

    _type = 'users'

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     blog_id: int, *target_ids: Union[int, str]):

        # Ищем по ID
        if target_ids:
            resp = await cls._c.select_by_id(
                conn, blog_id, tuple(map(int, target_ids)))

        # Возвращаем все
        else:
            resp = await cls._c.select(conn, blog_id)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, blog_id: int, fields: dict):

        # Проверка
        if (
            not await C.blog_owner(
                conn, user_id, blog_id) and
            not await C.blog_moder(
                conn, user_id, blog_id, 'manage_b') and
            not await C.admin(
                conn, user_id)
        ):
            raise Forbidden

        # Существует ли юзер
        if not await C.user(conn, fields['user_id']):
            raise ObjectNotFound

        # А не модер ли он?
        if await C.blog_moder(conn, fields['user_id'], blog_id):
            raise UserIsModer('ban', 'blog')
        if await C.fandom_moder(conn, fields['user_id'], fandom_id):
            raise UserIsModer('ban', 'fandom')

        try:
            await cls._c.e.insert(
                conn, fields['user_id'], blog_id,
                user_id, fields['reason'])
        except asyncpg.exceptions.UniqueViolationError:
            raise UserIsBanned('ban', 'blog')

    async def delete(self):

        # Проверка
        if (
            not await C.blog_owner(
                self._conn, self._uid, self.meta['blog_id']) and
            not await C.blog_moder(
                self._conn, self._uid, self.meta['blog_id']) and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._c.e.delete(self._conn, self.id, self.meta['blog_id'])


class Blog(Obj):
    _c = Commands(
        select="SELECT * FROM blogs ORDER BY id ASC",

        # args: fandom_id, blog_urls
        select_by_u_in_fandom="SELECT * FROM blogs "
                              "WHERE fandom_id = $1 "
                              "AND url = ANY($2::CITEXT[]) ORDER BY id ASC",

        # args: fandom_id, blog_ids
        select_by_id_in_fandom="SELECT * FROM blogs "
                               "WHERE fandom_id = $1"
                               "AND id = ANY($2::BIGINT[])  ORDER BY id ASC",

        # args: blog_ids
        select_by_id="SELECT * FROM blogs "
                     "WHERE id = ANY($1::BIGINT[]) ORDER BY id ASC",

        # args: fandom_id
        select_by_fandom="SELECT * FROM blogs "
                         "WHERE fandom_id = $1 ORDER BY id ASC",

        # args: user_id
        select_by_owner="SELECT * FROM blogs WHERE owner = $1 ORDER BY id ASC",

        # args: user_id, fandom_id, url, title, description, avatar
        insert="SELECT blogs_create($1, $2, $3, $4, $5, $6)",

        # args: edited_by, blog_id, title, description, avatar
        update="UPDATE blogs SET edited_by=$1, "
               "title=$3, description=$4, avatar=$5 WHERE id=$2",

        # args: blog_id
        history="SELECT * FROM blogs_history($1) ORDER BY edited_at DESC",
    )

    _type = 'blogs'

    @classmethod
    async def id_u(cls, request) -> 'Blog':
        conn = request.conn
        blog = request.match_info['blog']
        uid = request.uid

        try:
            return (await cls.select(conn, uid, 0, blog))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, *target_ids: Union[int, str],
                     u: bool=False) -> Tuple['Blog', ...]:

        # Ищем по url в фандоме
        if u and target_ids and fandom_id:
            resp = await cls._c.select_by_u_in_fandom(
                conn, fandom_id, target_ids)

        # Ищем по ID в фандоме
        elif target_ids and fandom_id:
            resp = await cls._c.select_by_id_in_fandom(
                conn, fandom_id, tuple(map(int, target_ids)))

        # Ищем по ID
        elif target_ids:
            resp = await cls._c.select_by_id(conn, tuple(map(int, target_ids)))

        # Ищем по фандому
        elif fandom_id:
            resp = await cls._c.select_by_fandom(conn, fandom_id)

        # Возвращаем все
        else:
            resp = await cls._c.select(conn)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def select_by_owner(cls, conn: asyncpg.connection.Connection,
                              user_id: int, target_id: int
                              ) -> Tuple['Blog', ...]:

        resp = await cls._c.select_by_owner(conn, target_id)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     fandom_id: int, fields: dict) -> int:

        # TODO: Больше проверок
        if (
            await C.fandom_banned(conn, user_id, fandom_id)
        ):
            raise Forbidden

        try:
            return await cls._c.v.insert(
                conn, user_id, fandom_id, fields['url'],
                fields['title'], fields['description'], fields['avatar'])
        except asyncpg.exceptions.UniqueViolationError:
            raise BlogUrlAlreadyTaken

    async def update(self, fields: dict):

        # Проверка
        if (
            self.attrs['owner'] != self._uid and
            not await C.blog_moder(
                self._conn, self._uid, self.id, 'edit_b') and
            not await C.fandom_moder(
                self._conn, self._uid, self.attrs['fandom_id'], 'edit_b') and
            not await C.admin(
                self._conn, self._uid)
        ):
            return Forbidden

        await self._c.e.update(
            self._conn, self._uid, self.id,
            fields['title'], fields['description'], fields['avatar'])

    async def history(self) -> Tuple['Blog', ...]:

        # Проверка
        if (
            self.attrs['owner'] != self._uid and
            not await C.blog_moder(
                self._conn, self._uid, self.id, 'edit_b') and
            not await C.fandom_moder(
                self._conn, self._uid, self.attrs['fandom_id'], 'edit_b') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._c.history(self._conn, self.id)

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

    # Posts

    async def posts_select(self, *target_ids: Union[int, str]
                           ) -> Tuple[Post, ...]:

        return await Post.select(
            self._conn, self._uid, self.id, 0, *target_ids)

    async def posts_insert(self, fields: dict) -> int:

        return await Post.insert(
            self._conn, self._uid, self.id, self.attrs['fandom_id'], fields)
