#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from . import checks as C
from .base import Obj, SelectResult, Commands
from ...web.exceptions import Forbidden, ObjectNotFound

__all__ = ('Comment', 'CommentVote')


class Comment(Obj):
    _c = Commands(
        select="SELECT * FROM comments ORDER BY id ASC",

        # args: comment_ids
        select_by_id="SELECT * FROM comments WHERE id = ANY($1::BIGINT[]) "
                     "ORDER BY id ASC",

        # args: post_id
        select_by_post="SELECT * FROM comments WHERE post_id = $1 "
                       "ORDER BY id ASC",

        # args: blog_id
        select_by_blog="SELECT * FROM comments WHERE blog_id = $1 "
                       "ORDER BY id ASC",

        # args: fandom_id
        select_by_fandom="SELECT * FROM comments WHERE fandom_id = $1 "
                         "ORDER BY id ASC",

        # args: user_id
        select_by_owner="SELECT * FROM comments WHERE owner = $1 "
                        "ORDER BY id ASC",

        # args: user_id, post_id, blog_id, fandom_id, parent_id, content
        insert="SELECT comments_create ($1, $2, $3, $4, $5, $6)",

        # args: user_id, post_id, content
        update="UPDATE comments SET edited_by=$1, content=$3 WHERE id = $2",

        # args: parent_id
        answers="SELECT * FROM comments WHERE parent_id = $1 ORDER BY id ASC",

        # args: post_id
        history="SELECT id, created_at, edited_at, edited_by, post_id, "
                "blog_id, fandom_id, owner, content "
                "FROM comments_history ($1) ORDER BY edited_at DESC"
    )

    _type = 'comments'
    _meta = ('votes_up', 'votes_down')

    @classmethod
    async def id_u(cls, request) -> 'Comment':
        conn = request.conn
        comment = request.match_info['comment']
        uid = request.uid

        try:
            return (await cls.select(conn, uid, 0, 0, 0, comment))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     post_id: int, blog_id: int, fandom_id: int,
                     *target_ids: Union[int, str]) -> Tuple['Comment', ...]:

        # Ищем по ID
        if target_ids:
            resp = await cls._c.select_by_id(conn, tuple(map(int, target_ids)))

        # Ищем по посту
        elif post_id:
            resp = await cls._c.select_by_post(conn, post_id)

        # Ищем по блогу
        elif post_id:
            resp = await cls._c.select_by_blog(conn, blog_id)

        # Ищем по фандому
        elif post_id:
            resp = await cls._c.select_by_fandom(conn, fandom_id)

        # Возвращаем все
        else:
            resp = await cls._c.select(conn)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def select_by_owner(cls, conn: asyncpg.connection.Connection,
                              user_id: int, target_id: int
                              ) -> Tuple['Comment', ...]:

        resp = await cls._c.select_by_owner(conn, target_id)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     post_id: int, blog_id: int, fandom_id: int,
                     parent_id: int, fields: dict
                     ) -> int:

        # Проверка
        if (
            not user_id or
            await C.blog_banned(conn, user_id, blog_id) or
            await C.fandom_banned(conn, user_id, fandom_id)
        ):
            raise Forbidden

        return await cls._c.v.insert(
            conn, user_id, post_id, blog_id, fandom_id, parent_id,
            fields['content'])

    async def update(self, fields: dict):

        # Проверка
        if (
            self.attrs['owner'] != self._uid and
            not await C.blog_owner(
                self._conn, self._uid, self.attrs['blog_id']) and
            not await C.blog_moder(
                self._conn, self._uid, self.attrs['blog_id'], 'edit_c') and
            not await C.fandom_moder(
                self._conn, self._uid, self.attrs['fandom_id'], 'edit_c') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        await self._c.e.update(
            self._conn, self._uid, self.id, fields['content'])

    async def answers(self) -> Tuple['Comment', ...]:

        resp = await self._c.answers(self._conn, self.id)

        return SelectResult(self.__class__(x) for x in resp)

    async def insert_answer(self, fields: dict) -> int:
        return await self.insert(
            self._conn, self._uid, self.attrs['post_id'],
            self.attrs['blog_id'], self.attrs['fandom_id'], self.id, fields)

    async def history(self) -> Tuple['Comment', ...]:

        # Проверка
        if (
            self.attrs['owner'] != self._uid and
            not await C.blog_owner(
                self._conn, self._uid, self.attrs['blog_id']) and
            not await C.blog_moder(
                self._conn, self._uid, self.attrs['blog_id'], 'edit_c') and
            not await C.fandom_moder(
                self._conn, self._uid, self.attrs['fandom_id'], 'edit_c') and
            not await C.admin(
                self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._c.history(self._conn, self.id)

        return SelectResult(self.__class__(x) for x in resp)

    # Votes

    async def votes_select(self) -> Tuple['CommentVote', ...]:
        return await CommentVote.select(self._conn, self._uid, self.id)

    async def votes_insert(self, fields: dict):
        await CommentVote.insert(
            self._conn, self._uid, self.id,
            self.arrts['blog_id'], self.attrs['fandom_id'], fields)


class CommentVote(Obj):
    _c = Commands(
        # args: comment_id
        select="SELECT u.*, cv.target_id AS comment_id, cv.vote "
               "FROM comment_votes AS cv "
               "INNER JOIN users AS u ON cv.user_id = u.id "
               "WHERE target_id = $1 ORDER BY cv.user_id ASC",

        # args: user_id, comment_id
        select_by_id="SELECT u.*, cv.target_id AS comment_id, cv.vote "
                     "FROM comment_votes AS cv "
                     "INNER JOIN users AS u ON cv.user_id = u.id "
                     "WHERE user_id = $1 AND target_id = $2",

        # args: user_id, target_id, vote
        insert="SELECT comments_vote ($1, $2, $3)"
    )

    _type = 'users'
    _meta = ('post_id', 'vote')

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, user_id: int,
                     comment_id: int) -> Tuple['CommentVote', ...]:

        # Только админам можно смотреть кто голосовал
        if await C.admin(conn, user_id):
            resp = await cls._c.select(conn, int(comment_id))
        else:
            resp = await cls._c.select_by_id(conn, user_id, int(comment_id))

        return SelectResult(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, user_id: int,
                     comment_id: int, blog_id: int, fandom_id: int,
                     fields: dict):

        # Проверка
        if (
            not user_id or
            await C.blog_banned(conn, user_id, blog_id) or
            await C.fandom_banned(conn, user_id, fandom_id)
        ):
            raise Forbidden

        await cls._c.insert(conn, user_id, comment_id, fields['vote'])
