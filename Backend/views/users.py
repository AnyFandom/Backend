#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, JsonResponse, validators as v
from ..utils.web.exceptions import ObjectNotFound, Forbidden

__all__ = ('UserList', 'User', 'UserHistory')


async def _id_u(request) -> m.User:
    conn = request.conn
    arg = request.match_info['arg']
    uid = request.uid

    try:
        if arg == 'current':
            if uid != 0:
                return (await m.User.select(conn, uid, uid))[0]
            else:
                raise Forbidden
        elif arg[:2] == 'u/':
            return (await m.User.select(conn, uid, arg[2:], u=True))[0]
        else:
            return (await m.User.select(conn, uid, arg))[0]
    except (IndexError, ValueError):
        raise ObjectNotFound


class UserList(BaseView):
    async def get(self):
        return JsonResponse(
            await m.User.select(self.request.conn, self.request.uid))


class User(BaseView):
    async def get(self):
        return JsonResponse(await _id_u(self.request))

    async def patch(self):
        body = await v.get_body(self.request, v.users.patch)
        await (await _id_u(self.request)).update(body)

        return JsonResponse()


class UserHistory(BaseView):
    async def get(self):
        resp = await (await _id_u(self.request)).history()

        return JsonResponse(resp)
