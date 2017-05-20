#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union, Tuple

import asyncpg

from .models_base import Obj
from ..web.exceptions import (Forbidden, ObjectNotFound, AlreadyModer,
                              AlreadyBanned, UserIsBanned, UserIsModer)


class User(Obj):
    _sqls = dict(
        select="SELECT * FROM users %s ORDER BY id ASC",

        # args: edited_by, user_id, description, avatar,
        update="UPDATE users SET edited_by=$1, "
               "description=$3, avatar=$4 WHERE id=$2",

        # args: user_id
        history="SELECT * FROM users_history ($1) ORDER BY id, edited_at ASC",

        # args: user_id
        check_exists="SELECT EXISTS (SELECT 1 FROM users WHERE id=$1)",

        # args: user_id
        check_admin="SELECT EXISTS (SELECT 1 FROM admins WHERE user_id=$1)"
    )

    @staticmethod
    def _map(data, meta) -> dict:
        resp = dict(type='users', id=data.pop('id'))

        if meta is not None:
            resp['meta'] = {x: data.pop(x) for x in meta if x in data}

        resp['attributes'] = data

        return resp

    @classmethod
    async def check_exists(cls, conn: asyncpg.connection.Connection,
                           user_id: int) -> bool:

        return await conn.fetchval(cls._sqls['check_exists'], user_id)

    @classmethod
    async def check_admin(cls, conn: asyncpg.connection.Connection,
                          user_id: int) -> bool:

        return await conn.fetchval(cls._sqls['check_admin'], user_id)

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
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self._data['id'],
            fields['description'], fields['avatar'])

    async def history(self) -> Tuple['User', ...]:

        # Проверка
        if (
            self._data['id'] != self._uid and
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self._data['id'])

        return tuple(self.__class__(x) for x in resp)


class FandomModer(User):
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
        update="UPDATE fandom_moders SET target_id=$2, edit_f=$3, "
               "manage_f=$4, ban_f=$5, create_b=$6, edit_b=$7, edit_p=$8, "
               "edit_c=$9 WHERE user_id=$1;",

        # args: user_id, fandom_id
        delete="DELETE FROM fandom_moders WHERE user_id=$1 AND target_id=$2",

        # args: user_id, fandom_id
        check_exists="SELECT EXISTS (SELECT 1 FROM fandom_moders "
                     "WHERE user_id=$1 AND target_id=$2 %s)"
    )

    # noinspection PyMethodOverriding
    @classmethod
    async def check_exists(cls, conn: asyncpg.connection.Connection,
                           user_id: int, fandom_id: int,
                           perm: str=None) -> bool:

        return await conn.fetchval(
            cls._sqls['check_exists'] % ('AND %s=TRUE', perm) if perm else '',
            user_id, fandom_id)

    # noinspection PyMethodOverriding
    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, fandom_id: int,
                     user_id: int, *target_ids: Union[int, str]
                     ) -> Tuple['FandomModer', ...]:

        if target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % 'AND fm.user_id = ANY($2::BIGINT[])',
                fandom_id, tuple(map(int, target_ids)))
        else:
            resp = await conn.fetch(cls._sqls['select'] % '', fandom_id)

        return tuple(cls(x, conn, user_id, cls._meta) for x in resp)

    # noinspection PyMethodOverriding
    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, fandom_id: int,
                     user_id: int, fields: dict):

        # Проверка
        if (
            not await FandomModer.check_exists(
                conn, user_id, fandom_id, 'manage_f') and
            not await User.check_admin(conn, user_id)
        ):
            raise Forbidden

        # Существует ли юзер
        if not await User.check_exists(conn, fields['user_id']):
            raise ObjectNotFound

        # А не забанен ли он?
        if await FandomBanned.check_exists(conn, fandom_id, fields['user_id']):
            raise UserIsBanned

        try:
            await conn.execute(
                cls._sqls['insert'],

                fields['user_id'], user_id,
                fields['edit_f'], fields['manage_f'], fields['ban_f'],
                fields['create_b'], fields['edit_b'],
                fields['edit_p'], fields['edit_c']
            )
        except asyncpg.exceptions.UniqueViolationError:
            raise AlreadyModer

    async def update(self, fields: dict):

        # Проверка
        if (
            not await FandomModer.check_exists(
                self._conn, self._uid, self._data['id'], 'manage_f') and
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'],

            self._data['id'], self._data['meta']['fandom_id'],
            fields['edit_f'], fields['manage_f'], fields['ban_f'],
            fields['create_b'], fields['edit_b'],
            fields['edit_p'], fields['edit_c'])

    async def delete(self):

        # Проверка
        if (
            not await FandomModer.check_exists(
                self._conn, self._uid, self._data['id'], 'manage_f') and
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['delete'],

            self._data['id'], self._data['meta']['fandom_id']
        )


class FandomBanned(User):
    _meta = ('fandom_id', 'set_by', 'reason')

    _sqls = dict(
        # args: fandom_id
        select="SELECT u.*, fb.target_id as fandom_id, fb.set_by, fb.reason "
               "FROM fandom_bans AS fb "
               "INNER JOIN users AS u ON fb.user_id=u.id "
               "WHERE fb.target_id=$1 %s ORDER BY u.id ASC",

        # args: user_id, fandom_id, set_by, reason
        insert="INSERT INTO fandom_bans (user_id, target_id, set_by, reason) "
               "VALUES ($1, $2, $3, $4);",

        # args: user_id, fandom_id
        delete="DELETE FROM fandom_bans WHERE user_id=$1 AND target_id=$2",

        # args: user_id, fandom_id
        check_exists="SELECT EXISTS (SELECT 1 FROM fandom_bans "
                     "WHERE user_id=$1 AND target_id=$2"
    )

    # noinspection PyMethodOverriding
    @classmethod
    async def check_exists(cls, conn: asyncpg.connection.Connection,
                           user_id: int, fandom_id: int):

        return await conn.fetchval(
            cls._sqls['check_exists'], user_id, fandom_id)

    # noinspection PyMethodOverriding
    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection, fandom_id: int,
                     user_id: int, *target_ids: Union[int, str]
                     ) -> Tuple['FandomBanned', ...]:

        if target_ids:
            resp = await conn.fetch(
                cls._sqls['select'] % 'AND fb.user_id = ANY($2::BIGINT[])',
                fandom_id, tuple(map(int, target_ids)))
        else:
            resp = await conn.fetch(cls._sqls['select'] % '', fandom_id)

        return tuple(cls(x, conn, user_id, cls._meta) for x in resp)

    # noinspection PyMethodOverriding
    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection, fandom_id: int,
                     user_id: int, fields: dict):

        # Проверка
        if (
            not await FandomModer.check_exists(
                conn, user_id, fandom_id, 'ban_f') and
            not await User.check_admin(conn, user_id)
        ):
            raise Forbidden

        # Существует ли юзер
        if not await User.check_exists(conn, fields['user_id']):
            raise ObjectNotFound

        # А не модер ли он?
        if await FandomModer.check_exists(conn, fields['user_id'], fandom_id):
            raise UserIsModer

        try:
            await conn.execute(
                cls._sqls['insert'],

                fields['user_id'], fandom_id,
                user_id, fields['reason'])
        except asyncpg.exceptions.UniqueViolationError:
            raise AlreadyBanned

    async def update(self, fields):
        pass

    async def delete(self):

        # Проверка
        if (
            not await FandomModer.check_exists(
                self._conn, self._uid, self._data['id'], 'ban_f') and
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['delete'],

            self._data['id'], self._data['meta']['fandom_id']
        )


class Fandom(Obj):
    _sqls = dict(
        select="SELECT * FROM fandoms %s ORDER BY id",

        # args: user_id, url, title, description, avatar
        insert="SELECT fandoms_create($1, $2, $3, $4, $5)",

        # args: edited_by, fandom_id, title, description, avatar
        update="UPDATE fandoms SET edited_by=$1,"
               "title=$3, description=$4, avatar=$5 WHERE id=$2",

        # args: fandom_id
        history="SELECT * FROM fandoms_history($1) ORDER BY id, edited_at ASC"
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
        if not await User.check_admin(conn, user_id):
            raise Forbidden

        new_id = await conn.fetchval(
            cls._sqls['insert'], user_id, fields['url'],
            fields['title'], fields['description'],
            fields['avatar'])

        return new_id

    async def update(self, fields: dict):

        # Проверка
        if (
            not await FandomModer.check_exists(
                self._conn, self._uid, self._data['id'], 'edit_f') and
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        await self._conn.execute(
            self._sqls['update'], self._uid, self._data['id'],
            fields['title'], fields['description'],
            fields['avatar'])

    async def history(self) -> Tuple['Fandom', ...]:

        # Проверка
        if (
            not await FandomModer.check_exists(
                self._conn, self._uid, self._data['id'], 'edit_f') and
            not await User.check_admin(self._conn, self._uid)
        ):
            raise Forbidden

        resp = await self._conn.fetch(self._sqls['history'], self._data['id'])

        return tuple(self.__class__(x) for x in resp)

    # Moders

    async def moders_select(self, *target_ids: Union[int, str]
                            ) -> Tuple[FandomModer, ...]:

        return await FandomModer.select(
            self._conn, self._data['id'], self._uid, *target_ids)

    async def moders_insert(self, fields: dict):

        await FandomModer.insert(
            self._conn, self._data['id'], self._uid, fields)

    # Bans

    async def bans_select(self, *target_ids: Union[int, str]
                          ) -> Tuple[FandomBanned, ...]:
        return await FandomBanned.select(
            self._conn, self._data['id'], self._uid, *target_ids)

    async def bans_insert(self, fields: dict):

        await FandomBanned.insert(
            self._conn, self._data['id'], self._uid, fields)
