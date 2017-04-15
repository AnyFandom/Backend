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
    def _map(data, meta) -> dict:
        resp = dict(type='users', id=data.pop('id'))

        if meta is not None:
            resp['meta'] = {x: data.pop(x) for x in meta if x in data}

        resp['attributes'] = data

        return resp

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
            not await self.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self._data['id'],
            fields.get('description'), fields.get('avatar'))

    async def history(self) -> Tuple['User', ...]:

        # Проверка
        if (
            self._data['id'] != self._uid and
            not await self.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self._data['id'])

        return tuple(self.__class__(x) for x in resp)


class Fandom(Obj):
    _sqls = dict(
        insert="SELECT fandoms_create($1, $2, $3, $4, $5)",
        select="SELECT * FROM fandoms %s ORDER BY id",
        update="UPDATE fandoms SET edited_by=$1,"
               "title=$3, description=$4, avatar=$5 WHERE id=$2",
        history="SELECT * FROM fandoms_history($1) ORDER BY id, edited_at ASC",

        moders_select=(
            "SELECT f.*, fm.set_by, fm.edit_f, fm.manage_f, fm.ban_f, "
            "fm.create_b,  fm.edit_b,  fm.remove_b, fm.edit_p, fm.remove_p,"
            "fm.edit_c,  fm.remove_c "
            "FROM fandoms AS f "
            "INNER JOIN fandom_moders AS fm ON fm.target_id=f.id"
        ),
    )

    @staticmethod
    def _map(data, meta) -> dict:
        resp = dict(type='fandoms', id=data.pop('id'))

        if meta is not None:
            resp['meta'] = {x: data.pop(x) for x in meta if x in data}

        resp['attributes'] = data

        return resp

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
        if not await cls.check_admin(conn, user_id):
            raise Forbidden

        new_id = await conn.fetchval(
            cls._sqls['insert'], user_id, fields.get('url'),
            fields.get('title'), fields.get('description'),
            fields.get('avatar'))

        return new_id

    async def update(self, fields: dict):

        # Проверка
        if (
            not await self.check_fandom_perm(
                self._conn, self._uid, self._data['id'], 'edit_f') and
            not await self.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self._data['id'],
            fields.get('title'), fields.get('description'),
            fields.get('avatar'))

    async def history(self) -> Tuple['Fandom', ...]:

        # Проверка
        if (
            not await self.check_fandom_perm(
                self._conn, self._uid, self._data['id'], 'edit_f') and
            not await self.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self._data['id'])

        return tuple(self.__class__(x) for x in resp)

    async def moders_select(self) -> Tuple[User, ...]:

        resp = await self._conn.fetch(self._sqls['moders_select'])
        meta = ('set_by', 'edit_f', 'manage_f', 'ban_f', 'create_b', 'edit_b',
                'remove_b', 'edit_p', 'remove_p', 'edit_c', 'remove_c')

        return tuple(User(x, self._conn, self._uid, meta) for x in resp)
