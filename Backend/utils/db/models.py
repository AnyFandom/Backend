#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Mapping
from typing import Union, Tuple
from abc import ABCMeta, abstractmethod

import asyncpg


class Obj(Mapping, metaclass=ABCMeta):
    def __init__(self, data):
        self._data = self._map(dict(data))

    # Mapping

    def __getitem__(self, item):
        return self._data[item]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    #########

    def __repr__(self):
        return '<%s[id=%i]' % (type(self).__name__, self._data['id'])

    @staticmethod
    @abstractmethod
    def _map(data):
        pass

    @classmethod
    @abstractmethod
    async def select(cls, conn, user_id, *target_ids):
        pass

    @classmethod
    @abstractmethod
    async def insert(cls, conn, user_id, fields):
        pass

    @abstractmethod
    async def update(self, conn, user_id, fields):
        pass


class User(Obj):
    _sqls = dict(
        select="SELECT * FROM users %s ORDER BY id ASC",
        update="UPDATE users SET edited_by=$1, "
               "description=$3, avatar=$4 WHERE id=$2",
        history="SELECT * FROM users_history($1) ORDER BY id, edited_at ASC",

        check=dict(
            update="SELECT users_update_check($1,$2)",
            history="SELECT users_history_check($1,$2)"
        )
    )

    @staticmethod
    def _map(data) -> dict:
        return dict(type='users', id=data.pop('id'), attributes=data)

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection,
                     user_id: int, *target_ids: Union[int, str],
                     u: bool=False) -> Tuple['User']:

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

        return tuple(map(cls, resp))

    @classmethod
    async def insert(cls, conn, user_id, fields):
        pass

    async def update(self, conn: asyncpg.connection.Connection,
                     user_id: int, fields: dict):
        # TODO: Убрать conn и user_id

        # Проверка
        await conn.execute(
            self._sqls['check']['update'], self._data['id'], user_id)

        await conn.execute(
            self._sqls['update'], user_id, self._data['id'],
            fields.get('description'), fields.get('avatar'))

    async def history(self, conn: asyncpg.connection.Connection,
                      user_id: int) -> Tuple['User']:
        # TODO: Убрать conn и user_id

        # Проверка
        await conn.execute(
            self._sqls['check']['history'], self._data['id'], user_id)

        resp = await conn.fetch(self._sqls['history'], self._data['id'])

        return tuple(map(self.__class__, resp))


class Fandom(Obj):
    _sqls = dict(
        insert="SELECT fandoms_create($1, $2, $3, $4, $5)",
        select="SELECT * FROM fandoms %s ORDER BY id",
        update="UPDATE fandoms SET edited_by=$1,"
               "title=$3, description=$4, avatar=$5 WHERE id=$2",

        check=dict(
            insert="SELECT fandoms_create_check($1)"
        )
    )

    @staticmethod
    def _map(data) -> dict:
        return dict(type='fandoms', id=data.pop('id'), attributes=data)

    @classmethod
    async def select(cls, conn: asyncpg.connection.Connection,
                     user_id: int, *target_ids: Union[int, str],
                     u: bool=False) -> Tuple['Fandom']:

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

        return tuple(map(cls, resp))

    @classmethod
    async def insert(cls, conn: asyncpg.connection.Connection,
                     user_id: int, fields: dict) -> int:

        # Проверка
        await conn.execute(cls._sqls['check']['insert'], user_id)

        new_id = await conn.fetchval(
            cls._sqls['insert'], user_id, fields.get('url'),
            fields.get('title'), fields.get('description'),
            fields.get('avatar'))

        return new_id

    async def update(self, conn, user_id, fields):
        pass
