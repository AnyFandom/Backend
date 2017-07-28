#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from . import checks as C
from .base import Obj, SelectResult, Commands
from ...web.exceptions import Forbidden, ObjectNotFound

from .blogs import Blog
from .posts import Post

__all__ = ('User',)


class User(Obj):
    _c = Commands(
        # args: offset
        select="SELECT * FROM users ORDER BY id LIMIT 20 OFFSET $1",

        # args: usernames
        select_by_u="SELECT * FROM users WHERE username = ANY($1::CITEXT[]) "
                    "ORDER BY id",

        # args: ids
        select_by_id="SELECT * FROM users WHERE id = ANY($1::BIGINT[]) "
                     "ORDER BY id",

        # args: edited_by, user_id, description, avatar
        update="UPDATE users SET edited_by=$1, description=$3, "
               "avatar=$4 WHERE id=$2",

        # args: user_id, offset
        history="SELECT * FROM users_history ($1) ORDER BY edited_at DESC "
                "LIMIT 20 OFFSET $2"
    )

    _type = 'users'

    @classmethod
    async def id_u(cls, request) -> 'User':
        conn = request.conn
        user = request.match_info['user']
        uid = request.uid

        try:
            if user == 'current':
                if uid != 0:
                    return (await cls.select(conn, uid, uid))[0]
                else:
                    raise Forbidden
            elif user[:2] == 'u/':
                return (await cls.select(conn, uid, user[2:], u=True))[0]
            else:
                return (await cls.select(conn, uid, user))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection,
                     user_id: int, *target_ids: Union[int, str],
                     u: bool=False, page: int=0) -> Tuple['User', ...]:

        # Ищем по имени
        if u and target_ids:
            resp = await cls._c.select_by_u(conn, target_ids)

        # Ищем по ID
        elif target_ids:
            resp = await cls._c.select_by_id(conn, tuple(map(int, target_ids)))

        # Возвращаем все
        else:
            resp = await cls._c.select(conn, page * 20)

        return SelectResult(cls(x, conn, user_id) for x in resp)

    async def update(self, fields: dict):

        # Проверка
        if (
            self.id != self._uid and
            not await C.admin(self._conn, self._uid)
        ):
            raise Forbidden

        await self._c.e.update(
            self._conn, self._uid, self.id,
            fields['description'], fields['avatar'])

    async def history(self) -> Tuple['User', ...]:

        # Проверка
        if (
            self.id != self._uid and
            not await C.admin(self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._c.history(self._conn, self.id)

        return SelectResult(self.__class__(x) for x in resp)

    async def blogs(self) -> Tuple[Blog, ...]:
        return await Blog.select_by_owner(self._conn, self._uid, self.id)

    async def posts(self) -> Tuple[Post, ...]:
        return await Post.select_by_owner(self._conn, self._uid, self.id)
