#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Mapping
from abc import ABCMeta, abstractmethod


class Obj(Mapping, metaclass=ABCMeta):
    def __init__(self, data, conn=None, user_id=None, meta=None):
        self._data = self._map(dict(data), meta)
        self._conn = conn
        self._uid = user_id
        self._meta = meta

    # Mapping

    def __getitem__(self, item):
        return self._data[item]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    #########

    def __repr__(self):
        return '<%s id=%i>' % (type(self).__name__, self._data['id'])

    @staticmethod
    @abstractmethod
    def _map(data, meta):
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
