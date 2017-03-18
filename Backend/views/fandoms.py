#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils import db
from ..utils.web import BaseView, JsonResponse, validators as v
from ..utils.web.exceptions import ObjectDoesNotExists, Forbidden, NotYetImplemented


async def _id_u(request) -> dict:
    conn = request.conn
    first = request.match_info['first']
    second = request.match_info.get('second', None)

    try:
        if first == 'u' and second is not None:
            return (await db.fandoms.get(conn, second, u=True))[0]
        else:
            return (await db.fandoms.get(conn, first))[0]
    except (IndexError, ValueError):
        raise ObjectDoesNotExists


class FandomListView(BaseView):
    async def get(self):
        return JsonResponse(await db.fandoms.get(self.request.conn))

    async def post(self):
        if self.request.uid == 0:
            raise Forbidden

        body = await v.get_body(self.request, v.fandoms.add)

        new_id = await db.fandoms.add(self.request.conn, self.request.uid,
                                      body['title'], body['url'],
                                      body['description'], body['avatar'])

        return JsonResponse(
            {'Location': '/fandoms/%i' % new_id}, status_code=201,
            headers={'Location': '/fandoms/%i' % new_id}
        )


class FandomView(BaseView):
    async def get(self):
        return JsonResponse(await _id_u(self.request))

    async def patch(self):
        raise NotYetImplemented
