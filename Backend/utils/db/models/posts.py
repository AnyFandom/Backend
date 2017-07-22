#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from . import checks as C
from .base import Obj, SelectResult
from ...web.exceptions import Forbidden, ObjectNotFound

__all__ = ('Post',)


class Post(Obj):
    _sqls = dict(
        select="SELECT * FROM blogs %s ORDER BY id ASC",

        # args: user_id, blog_id, fandom_id, title, content
        insert="SELECT posts_create($1, $2, $3, $4, $5)",

        # args: user_id, post_id, title, content
        update="UPDATE posts SET edited_by=$1, "
               "title=$3, content=$4 WHERE id=$2",

        # args: post_id
        history="SELECT * FROM posts_history($1) ORDER BY edited_by DESC"
    )

    _type = 'posts'

    @classmethod
    async def id_u(cls, request) -> 'Post':
        conn = request.conn
        post = request.match_info['post']
        uid = request.uid

        try:
            return (await cls.select(conn, uid, 0, 0, post))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     blog_id: int, fandom_id: int,
                     *target_ids: Union[int, str]) -> Tuple['Post', ...]:

        assert (blog_id and fandom_id) or (not blog_id and not fandom_id),\
            'blog_id или fandom_id, НЕ ОБА'

        # Ищем по ID в блоге
        if target_ids and blog_id:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[]) "
                                      "AND blog_id = $2",
                tuple(map(int, target_ids)), blog_id)

        # Ищем по ID в фандоме
        elif target_ids and fandom_id:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[]) "
                                      "AND fandom_id = $2",
                tuple(map(int, target_ids)), fandom_id)

        # Ищем по ID
        elif target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[])",
                tuple(map(int, target_ids)))

        # Ищем по блогу
        elif blog_id:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE blog_id = $1", blog_id)

        # Ищем по фандому
        elif fandom_id:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE fandom_id = $1", fandom_id)

        # Возвращаем все
        else:
            resp = await conn.fetch(cls._sqls['select'] % "")

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def select_by_owner(cls, conn: asyncpg.connection.Connection,
                              user_id: int, target_id: int
                              ) -> Tuple['Post', ...]:

        resp = await conn.fetch(
            cls._sqls['select'] % "WHERE owner = $1", target_id)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     blog_id: int, fandom_id: int, fields: dict) -> int:

        if (
            not user_id or
            await C.blog_banned(conn, user_id, blog_id) or
            await C.fandom_banned(conn, user_id, fandom_id)
        ):
            raise Forbidden

        return await conn.fetchval(
            cls._sqls['insert'], user_id, blog_id, fandom_id,
            fields['title'], fields['content'])

    async def update(self, fields: dict):

        # Проверка
        if (
            self.id != self._uid and
            not await C.blog_owner(
                self._conn, self._uid, self.attrs['blog_id']) and
            not await C.blog_moder(
                self._conn, self._uid, self.attrs['blog_id'], 'edit_p') and
            not await C.fandom_moder(
                self._conn, self._uid, self.attrs['fandom_id'], 'edit_p') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self.id,
            fields['title'], fields['content'])

    async def history(self) -> Tuple['Post', ...]:

        # Проверка
        if (
            self.id != self._uid and
            not await C.blog_owner(
                self._conn, self._uid, self.attrs['blog_id']) and
            not await C.blog_moder(
                self._conn, self._uid, self.attrs['blog_id'], 'edit_p') and
            not await C.fandom_moder(
                self._conn, self._uid, self.attrs['fandom_id'], 'edit_p') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self.id)

        return SelectResult(self.__class__(x) for x in resp)

    # Votes

    async def votes_select(self) -> Tuple['PostVote', ...]:
        return await PostVote.select(self._conn, self._uid, self.id)

    async def votes_insert(self, fields: dict):
        await PostVote.insert(
            self._conn, self._uid, self.id,
            self.attrs['blog_id'], self.attrs['fandom_id'], fields)


class PostVote(Obj):
    _meta = ('post_id', 'vote')

    _sqls = dict(
        # args: post_id
        select="SELECT u.*, pv.target_id AS post_id, pv.vote "
               "FROM posts_votes AS pv "
               "INNER JOIN users AS u ON pv.user_id=u.id "
               "WHERE target_id=$1 %s ORDER BY pv.user_id ASC",

        # args: post_id
        select_short="SELECT COUNT(*) filter (WHERE vote) AS up, "
                     "COUNT(*) filter (WHERE NOT vote) AS down "
                     "WHERE target_id=$1",

        # args: user_id, post_id, vote
        insert="INSERT INTO posts_votes AS pv (user_id, target_id, vote)"
               "VALUES ($1, $2, $3) "
               "ON CONFLICT (target_id, user_id) DO "
               "UPDATE SET vote=EXCLUDED.vote "
               "WHERE pv.target_id=EXCLUDED.target_id "
               "AND pv.user_id=EXCLUDED.user_id"
    )

    _type = 'users'

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     post_id: Union[int, str]) -> Tuple['PostVote', ...]:

        # Только админам можно смотреть кто голосовал
        if await C.admin(conn, user_id):
            resp = await conn.fetch(cls._sqls['select'] % '', int(post_id))
        else:
            resp = await conn.fetch(cls._sqls['select'] % 'AND user_id=$2',
                                    int(post_id), user_id)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     post_id: int, blog_id: int, fandom_id: int, fields: dict):

        if (
            not user_id or
            await C.blog_banned(conn, user_id, blog_id) or
            await C.fandom_banned(conn, user_id, fandom_id)
        ):
            raise Forbidden

        await conn.execute(
            cls._sqls['insert'], user_id, post_id, fields['vote'])
