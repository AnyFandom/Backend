#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple
from collections import Mapping
from abc import ABCMeta, abstractmethod

import asyncpg


class Obj(Mapping, metaclass=ABCMeta):
    def __init__(self, data, conn=None, user_id=None):
        self._data = self._map(dict(data))
        self._conn = conn
        self._uid = user_id

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
    async def check_admin(conn: asyncpg.connection.Connection,
                          user_id: int) -> bool:

        return await conn.fetchval(
            'SELECT EXISTS (SELECT 1 FROM admins WHERE user_id=$1)', user_id)

    @staticmethod
    async def check_fandom_perm(conn: asyncpg.connection.Connection,
                                user_id: int, target_id: int,
                                perm: str) -> bool:

        return await conn.fetchval(
            'SELECT EXISTS (SELECT 1 FROM fandom_staff '
            'WHERE user_id=$1 AND target_id=$2 AND %s=TRUE)' % perm,
            user_id, target_id
        )

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
    async def update(self, fields):
        pass
