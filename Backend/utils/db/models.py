#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from .models_base import Obj
from ..web.exceptions import Forbidden


class User(Obj):
    _sqls = dict(
        select="SELECT * FROM users %s ORDER BY id ASC",
        update="UPDATE users SET edited_by=$1, "
               "description=$3, avatar=$4 WHERE id=$2",
        history="SELECT * FROM users_history ($1) ORDER BY id, edited_at ASC",
    )

    @staticmethod
    def _map(data) -> dict:
        return dict(type='users', id=data.pop('id'), attributes=data)

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection,
                     user_id: int, *target_ids: Union[int, str],
                     u: bool=False) -> Tuple['User', ...]:

        # На вход поданы имена
        if u and target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE username = ANY($1::CITEXT[])",
                target_ids)

        # На вход поданы ID
        elif target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[])",
                tuple(map(int, target_ids)))

        # На вход не подано ничего
        else:
            resp = await conn.fetch(cls._sqls['select'] % '')

        return tuple(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn, user_id, fields):
        pass

    async def update(self, fields: dict):

        # Проверка
        if (
            self._data['id'] != self._uid and
            not await self.check(
                self._conn, 'site', 0, self._uid, ('admin', 'moder'))
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self._data['id'],
            fields.get('description'), fields.get('avatar'))

    async def history(self) -> Tuple['User', ...]:

        # Проверка
        if (
            self._data['id'] != self._uid and
            not await self.check(
                self._conn, 'site', 0, self._uid, ('admin', 'moder'))
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self._data['id'])

        return tuple(map(self.__class__, resp))


class Fandom(Obj):
    _sqls = dict(
        insert="SELECT fandoms_create($1, $2, $3, $4, $5)",
        select="SELECT * FROM fandoms %s ORDER BY id",
        update="UPDATE fandoms SET edited_by=$1,"
               "title=$3, description=$4, avatar=$5 WHERE id=$2",
        history="SELECT * FROM fandoms_history($1) ORDER BY id, edited_at ASC",
    )

    @staticmethod
    def _map(data) -> dict:
        return dict(type='fandoms', id=data.pop('id'), attributes=data)

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection,
                     user_id: int, *target_ids: Union[int, str],
                     u: bool=False) -> Tuple['Fandom', ...]:

        # На вход поданы url
        if u and target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE url = ANY($1::CITEXT[])",
                target_ids)

        # На вход поданы ID
        elif target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % "WHERE id = ANY($1::BIGINT[])",
                tuple(map(int, target_ids)))

        # На вход не подано ничего
        else:
            resp = await conn.fetch(cls._sqls['select'] % '')

        return tuple(cls(x, conn, user_id) for x in resp)

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection,
                     user_id: int, fields: dict) -> int:

        # Проверка
        if not await cls.check(conn, 'site', 0, user_id, ('admin',)):
            raise Forbidden

        new_id = await conn.fetchval(
            cls._sqls['insert'], user_id, fields.get('url'),
            fields.get('title'), fields.get('description'),
            fields.get('avatar'))

        return new_id

    async def update(self, fields: dict):

        # Проверка
        if (
            not await self.check(
                self._conn, 'fandom', self._data['id'],
                self._uid, ('admin',)) and
            not await self.check(
                self._conn, 'site', 0, self._uid, ('admin', 'moder'))
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self._data['id'],
            fields.get('title'), fields.get('description'),
            fields.get('avatar'))

    async def history(self) -> Tuple['Fandom', ...]:

        # Проверка
        if (
            not await self.check(
                self._conn, 'fandom', self._data['id'],
                self._uid, ('admin',)) and
            not await self.check(
                self._conn, 'site', 0, self._uid, ('admin', 'moder'))
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self._data['id'])

        return tuple(map(self.__class__, resp))
