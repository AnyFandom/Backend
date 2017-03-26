#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, JsonResponse, validators as v
from ..utils.web.exceptions import ObjectDoesNotExists, Forbidden


async def _id_u(request) -> m.User:
    conn = request.conn
    first = request.match_info['first']
    second = request.match_info.get('second', None)
    uid = request.uid

    try:
        if first == 'current':
            if uid != 0:
                return (await m.User.select(conn, uid, uid))[0]
            else:
                raise Forbidden
        elif first == 'u' and 'second' is not None:
            return (await m.User.select(conn, uid, second, u=True))[0]
        else:
            return (await m.User.select(conn, uid, first))[0]
    except (IndexError, ValueError):
        raise ObjectDoesNotExists


class UserListView(BaseView):
    async def get(self):
        return JsonResponse(
            await m.User.select(self.request.conn, self.request.uid))


class UserView(BaseView):
    async def get(self):
        return JsonResponse(await _id_u(self.request))

    async def patch(self):
        body = await v.get_body(self.request, v.users.patch)
        await (await _id_u(self.request)).update(body)

        return JsonResponse()


class UserHistoryView(BaseView):
    async def get(self):
        resp = await (await _id_u(self.request)).history()

        return JsonResponse(resp)
