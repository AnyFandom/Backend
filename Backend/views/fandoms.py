#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils import db
from ..utils.db import models as m
from ..utils.web import BaseView, JsonResponse, validators as v
from ..utils.web.exceptions import ObjectNotFound, Forbidden, NotYetImplemented


async def _id_u(request) -> m.Fandom:
    conn = request.conn
    first = request.match_info['first']
    second = request.match_info.get('second', None)
    uid = request.uid

    try:
        if first == 'u' and second is not None:
            return (await m.Fandom.select(conn, uid, second, u=True))[0]
        else:
            return (await m.Fandom.select(conn, uid, first))[0]
    except (IndexError, ValueError):
        raise ObjectNotFound


class FandomListView(BaseView):
    async def get(self):
        return JsonResponse(
            await m.Fandom.select(self.request.conn, self.request.uid))

    async def post(self):
        body = await v.get_body(self.request, v.fandoms.add)

        new_id = await m.Fandom.insert(
            self.request.conn, self.request.uid, body)

        return JsonResponse(
            {'Location': '/fandoms/%i' % new_id}, status_code=201,
            headers={'Location': '/fandoms/%i' % new_id}
        )


class FandomView(BaseView):
    async def get(self):
        return JsonResponse(await _id_u(self.request))

    async def patch(self):
        body = await v.get_body(self.request, v.fandoms.patch)
        await (await _id_u(self.request)).update(body)

        return JsonResponse()


class FandomHistoryView(BaseView):
    async def get(self):
        resp = await (await _id_u(self.request)).history()

        return JsonResponse(resp)
