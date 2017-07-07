#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Mapping
from abc import ABCMeta, abstractmethod


# Страшный костыль
class SelectResult(tuple):
    pass


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

    @property
    def id(self):
        return self._data['id']

    @property
    def attrs(self):
        return self._data['attributes']

    @property
    def meta(self):
        return self._data['meta']

    def __repr__(self):
        return '<%s id=%i>' % (type(self).__name__, self.id)

    _type = ''

    @classmethod
    def _map(cls, data, meta) -> dict:
        resp = dict(type=cls._type, id=data.pop('id'))

        if meta is not None:
            resp['meta'] = {x: data.pop(x) for x in meta if x in data}

        resp['attributes'] = data

        return resp

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
