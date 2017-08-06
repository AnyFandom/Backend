#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


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
            _m = {x: data.pop(x) for x in cls._meta if x in data}
            if _m:
                resp['meta'] = _m

        resp['attributes'] = data

        return resp


class Commands:
    def __new__(cls, __type: int=0, **sqls: str):
        if __type == 0:
            action = 'fetch'
        elif __type == 1:
            action = 'execute'
        elif __type == 2:
            action = 'fetchval'
        else:
            action = 'fetchrow'

        definition = 'class _Commands:\n'

        for (key, val) in sqls.items():
            definition += f'    @staticmethod\n' \
                          f'    async def {key}(conn, *args):\n' \
                          f'        return await conn.{action}(\n' \
                          f'            {repr(val)}, *args\n' \
                          f'        )\n\n'

        if __type == 0:
            definition += f'    e = Commands(1, **{str(sqls)})\n'\
                          f'    v = Commands(2, **{str(sqls)})\n'\
                          f'    r = Commands(3, **{str(sqls)})\n'

        local = dict()

        exec(definition, globals(), local)
        result = local['_Commands']

        return result

