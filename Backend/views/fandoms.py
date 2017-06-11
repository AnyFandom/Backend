#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, JsonResponse, validators as v
from ..utils.web.exceptions import ObjectNotFound

__all__ = ('FandomList', 'Fandom', 'FandomHistory',
           'FandomModerList', 'FandomModer',
           'FandomBansList', 'FandomBans')


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
        return JsonResponse(await m.Fandom.id_u(self.request))

    async def patch(self):
        body = await v.get_body(self.request, v.fandoms.update)
        await (await m.Fandom.id_u(self.request)).update(body)

        return JsonResponse()


class FandomHistory(BaseView):
    async def get(self):
        resp = await (await m.Fandom.id_u(self.request)).history()

        return JsonResponse(resp)


class FandomModerList(BaseView):
    async def get(self):
        resp = await (await m.Fandom.id_u(self.request)).moders_select()

        return JsonResponse(resp)

    async def post(self):
        body = await v.get_body(self.request, v.fandoms.moders_insert)
        await (await m.Fandom.id_u(self.request)).moders_insert(body)

        return JsonResponse(status_code=201)


class FandomModer(BaseView):
    async def get(self):
        try:
            resp = (await (await m.Fandom.id_u(self.request)).moders_select(
                self.request.match_info['moder']))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

        return JsonResponse(resp)

    async def patch(self):
        body = await v.get_body(self.request, v.fandoms.moders_update)
        await (await (await m.Fandom.id_u(self.request)).moders_select(
            self.request.match_info['moder']))[0].update(body)

        return JsonResponse()

    async def delete(self):
        await (await (await m.Fandom.id_u(self.request)).moders_select(
            self.request.match_info['moder']))[0].delete()

        return JsonResponse()


class FandomBansList(BaseView):
    async def get(self):
        resp = await (await m.Fandom.id_u(self.request)).bans_select()

        return JsonResponse(resp)

    async def post(self):
        body = await v.get_body(self.request, v.fandoms.bans_insert)
        await (await m.Fandom.id_u(self.request)).bans_insert(body)

        return JsonResponse(status_code=201)


class FandomBans(BaseView):
    async def get(self):
        try:
            resp = (await (await m.Fandom.id_u(self.request)).bans_select(
                self.request.match_info['banned']))[0]
        except (IndexError, ValueError):
            raise ObjectNotFound

        return JsonResponse(resp)

    async def delete(self):
        await (await (await m.Fandom.id_u(self.request)).bans_select(
            self.request.match_info['banned']))[0].delete()

        return JsonResponse()
