#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncpg

from ..utils import db
from ..utils.web import BaseView, JsonResponse, validators as v
from ..utils.web.exceptions import UserDoesNotExists, Forbidden


async def _id_u(request) -> dict:
    conn = request.conn
    first = request.match_info['first']
    second = request.match_info.get('second', None)
    uid = request.uid

    try:
        if first == 'current':
            if uid is not None:
                return (await db.users.get(conn, uid))[0]
            else:
                raise Forbidden
        elif first == 'u' and 'second' is not None:
            return (await db.users.get(conn, second, u=True))[0]
        else:
            return (await db.users.get(conn, first))[0]
    except (IndexError, ValueError):
        raise UserDoesNotExists


class UserListView(BaseView):
    async def get(self):
        return JsonResponse(await db.users.get(self.request.conn))


class UserView(BaseView):
    async def get(self):
        return JsonResponse(await _id_u(self.request))

    async def patch(self):
        if self.request.uid == 0:
            raise Forbidden
        body = await v.get_body(self.request, v.users.patch)
        await db.users.patch(self.request.conn, self.request.uid,
                             (await _id_u(self.request))['id'], body)

        return JsonResponse()


class UserHistoryView(BaseView):
    async def get(self):
        resp = await db.users.get_history(self.request.conn, self.request.uid,
                                          (await _id_u(self.request))['id'])
        if not resp:
            raise Forbidden
        return JsonResponse(resp)
