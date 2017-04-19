#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, JsonResponse, validators as v
from ..utils.web.exceptions import ObjectNotFound

__all__ = ('FandomList', 'Fandom', 'FandomHistory', 'FandomModers')


async def _id_u(request) -> m.Fandom:
    conn = request.conn
    arg = request.match_info['arg']
    uid = request.uid

    try:
        if arg[:2] == 'u/':
            return (await m.Fandom.select(conn, uid, arg[2:], u=True))[0]
        else:
            return (await m.Fandom.select(conn, uid, arg))[0]
    except (IndexError, ValueError):
        raise ObjectNotFound


class FandomList(BaseView):
    async def get(self):
        return JsonResponse(
            await m.Fandom.select(self.request.conn, self.request.uid))

    async def post(self):
        body = await v.get_body(self.request, v.fandoms.insert)

        new_id = await m.Fandom.insert(
            self.request.conn, self.request.uid, body)

        return JsonResponse(
            {'Location': '/fandoms/%i' % new_id}, status_code=201,
            headers={'Location': '/fandoms/%i' % new_id}
        )


class Fandom(BaseView):
    async def get(self):
        return JsonResponse(await _id_u(self.request))

    async def patch(self):
        body = await v.get_body(self.request, v.fandoms.patch)
        await (await _id_u(self.request)).update(body)

        return JsonResponse()


class FandomHistory(BaseView):
    async def get(self):
        resp = await (await _id_u(self.request)).history()

        return JsonResponse(resp)


class FandomModers(BaseView):
    async def get(self):
        resp = await (await _id_u(self.request)).moders_select()

        return JsonResponse(resp)

