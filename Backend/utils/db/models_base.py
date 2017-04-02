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
    async def check(conn: asyncpg.connection.Connection,
                    target_type: str, target_id: int,
                    user_id: int, roles: Tuple[str, ...]) -> bool:

        return await conn.fetchval(
            'SELECT check_rels ($1, $2, $3, $4)',
            target_type, target_id, user_id, roles
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
