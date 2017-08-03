#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Страшный костыль
class SelectResult(tuple):
    pass


class Obj:
    def __init__(self, data, conn=None, user_id=None):
        self._data = self._map(dict(data))
        self._conn = conn
        self._uid = user_id

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
        return f'<{type(self).__name__} id={self.id}>'

    _type = ''
    _meta: tuple = None

    @classmethod
    def _map(cls, data: dict) -> dict:
        resp = dict(type=cls._type, id=data.pop('id'))

        if cls._meta is not None:
            resp['meta'] = {x: data.pop(x) for x in cls._meta if x in data}

        resp['attributes'] = data

        return resp


class Commands:
    def __init__(self, __type=0, **sqls: str):
        self._sqls = sqls
        self._type = __type

        if __type == 0:  # fetch
            self.e = Commands(1, **sqls)  # execute
            self.v = Commands(2, **sqls)  # fetchval
            self.r = Commands(3, **sqls)  # fetchrow

    def __getattr__(self, item):
        async def func(conn, *args):

            if self._type == 0:
                return await conn.fetch(self._sqls[item], *args)
            elif self._type == 1:
                return await conn.execute(self._sqls[item], *args)
            elif self._type == 2:
                return await conn.fetchval(self._sqls[item], *args)
            else:
                return await conn.fetchrow(self._sqls[item], *args)

        return func

