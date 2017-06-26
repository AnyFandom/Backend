#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, JsonResponse, validators as v
from ..utils.web.exceptions import ObjectNotFound

__all__ = ('FandomList', 'Fandom', 'FandomHistory',
           'FandomModerList', 'FandomModer',
           'FandomBannedList', 'FandomBanned',
           'FandomBlogList', 'FandomBlog')


class FandomList(BaseView):
    async def get(self):
        return JsonResponse(
            await m.Fandom.select(self.request.conn, self.request.uid))

    @v.get_body(v.fandoms.insert)
    async def post(self, body):
        new_id = await m.Fandom.insert(
            self.request.conn, self.request.uid, body)

        loc = '/fandoms/%i' % new_id

        return JsonResponse(
            {'Location': loc}, status_code=201, headers={'Location': loc})


class Fandom(BaseView):
    async def get(self):
        return JsonResponse(await m.Fandom.id_u(self.request))

    @v.get_body(v.fandoms.update)
    async def patch(self, body):
        await (await m.Fandom.id_u(self.request)).update(body)

        return JsonResponse()


class FandomHistory(BaseView):
    async def get(self):
        return JsonResponse(
            await (await m.Fandom.id_u(self.request)).history())


class FandomModerList(BaseView):
    async def get(self):
        return JsonResponse(
            await (await m.Fandom.id_u(self.request)).moders_select())

    @v.get_body(v.fandoms.moders_insert)
    async def post(self, body):
        ids = await (await m.Fandom.id_u(self.request)).moders_insert(body)

        loc = '/fandoms/%i/moders/%i' % ids

        return JsonResponse(
            {'Location': loc}, status_code=201, headers={'Location': loc})


class FandomModer(BaseView):
    async def get(self):
        try:
            return JsonResponse(
                (await (await m.Fandom.id_u(self.request)).moders_select(
                    self.request.match_info['moder']))[0]
            )
        except (IndexError, ValueError):
            raise ObjectNotFound

    @v.get_body(v.fandoms.moders_update)
    async def patch(self, body):
        await (await (await m.Fandom.id_u(self.request)).moders_select(
            self.request.match_info['moder']))[0].update(body)

        return JsonResponse()

    async def delete(self):
        await (await (await m.Fandom.id_u(self.request)).moders_select(
            self.request.match_info['moder']))[0].delete()

        return JsonResponse()


class FandomBannedList(BaseView):
    async def get(self):
        return JsonResponse(
            await (await m.Fandom.id_u(self.request)).bans_select())

    @v.get_body(v.fandoms.bans_insert)
    async def post(self, body):
        ids = await (await m.Fandom.id_u(self.request)).bans_insert(body)

        loc = '/fandoms/%i/bans/%i' % ids

        return JsonResponse(
            {'Location': loc}, status_code=201, headers={'Location': loc})


class FandomBanned(BaseView):
    async def get(self):
        try:
            return JsonResponse(
                (await (await m.Fandom.id_u(self.request)).bans_select(
                    self.request.match_info['banned']))[0]
            )
        except (IndexError, ValueError):
            raise ObjectNotFound

    async def delete(self):
        await (await (await m.Fandom.id_u(self.request)).bans_select(
            self.request.match_info['banned']))[0].delete()

        return JsonResponse()


class FandomBlogList(BaseView):
    async def get(self):
        return JsonResponse(
            await (await m.Fandom.id_u(self.request)).blogs_select())

    @v.get_body(v.blogs.insert)
    async def post(self, body):
        new_id = await (await m.Fandom.id_u(self.request)).blogs_insert(body)

        loc = '/blogs/%i' % new_id

        return JsonResponse(
            {'Location': loc}, status_code=201, headers={'Location': loc})


class FandomBlog(BaseView):
    async def get(self):
        return JsonResponse(
            await (await m.Fandom.id_u(self.request)).blogs_id_u(self.request))
