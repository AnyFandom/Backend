#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m, postgres
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('FandomList', 'Fandom', 'FandomHistory',
           'FandomModerList', 'FandomModer',
           'FandomBannedList', 'FandomBanned',
           'FandomBlogList', 'FandomBlog',
           'FandomPostList', 'FandomCommentList')


class FandomList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await m.Fandom.select(self.request.conn, self.request.uid)

    @json_response
    @v.get_body(v.fandoms.insert)
    @postgres
    async def post(self, body):
        new_id = await m.Fandom.insert(
            self.request.conn, self.request.uid, body)

        loc = f'/fandoms/{new_id}'

        return {'Location': loc}, 201, {'Location': loc}


class Fandom(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await m.Fandom.id_u(self.request)

    @json_response
    @v.get_body(v.fandoms.update)
    @postgres
    async def patch(self, body):
        await (await m.Fandom.id_u(self.request)).update(body)


class FandomHistory(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).history()


class FandomModerList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).moders_select()

    @json_response
    @v.get_body(v.fandoms.moders_insert)
    @postgres
    async def post(self, body):
        ids = await (await m.Fandom.id_u(self.request)).moders_insert(body)
        loc = f'/fandoms/{ids[0]}/moders/{ids[1]}'

        return {'Location': loc}, 201, {'Location': loc}


class FandomModer(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).moders_id_u(
            self.request)

    @json_response
    @v.get_body(v.fandoms.moders_update)
    @postgres
    async def patch(self, body):
        await (await (await m.Fandom.id_u(self.request)).moders_id_u(
            self.request)).update(body)

    @json_response
    @postgres
    async def delete(self):
        await (await (await m.Fandom.id_u(self.request)).moders_id_u(
            self.request)).delete()


class FandomBannedList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).bans_select()

    @json_response
    @v.get_body(v.fandoms.bans_insert)
    @postgres
    async def post(self, body):
        ids = await (await m.Fandom.id_u(self.request)).bans_insert(body)
        loc = f'/fandoms/{ids[0]}/bans/{ids[1]}'

        return {'Location': loc}, 201, {'Location': loc}


class FandomBanned(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).bans_id_u(
            self.request)

    @json_response
    @postgres
    async def delete(self):
        await (await (await m.Fandom.id_u(self.request)).bans_id_u(
            self.request)).delete()


class FandomBlogList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).blogs_select()

    @json_response
    @v.get_body(v.blogs.insert)
    @postgres
    async def post(self, body):
        new_id = await (await m.Fandom.id_u(self.request)).blogs_insert(body)
        loc = f'/blogs/{new_id}'

        return {'Location': loc}, 201, {'Location': loc}


class FandomBlog(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).blogs_id_u(
            self.request)


class FandomPostList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).posts_select()


class FandomCommentList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Fandom.id_u(self.request)).comments_select()
