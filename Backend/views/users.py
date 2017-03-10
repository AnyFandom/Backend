#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncpg

from ..utils import db
from ..utils.web import BaseView, JsonResponse
from ..utils.web.exceptions import UserDoesNotExists, Forbidden


async def _id_u(request) -> dict:
    conn = request.conn
    first = request.match_info['first']
    second = request.match_info.get('second', None)
    uid = request.uid

    try:
        if first == 'current':
            if uid is not None:
                return (await db.users.get_users(conn, uid))[0]
            else:
                raise Forbidden
        elif first == 'u' and 'second' is not None:
            return (await db.users.get_users(conn, second, u=True))[0]
        else:
            return (await db.users.get_users(conn, first))[0]
    except (IndexError, ValueError):
        raise UserDoesNotExists


class UserListView(BaseView):
    async def get(self):
        return JsonResponse(await db.users.get_users(self.request.conn))


class UserView(BaseView):
    async def get(self):
        return JsonResponse(await _id_u(self.request))
