#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('BlogList', 'Blog', 'BlogHistory',
           'BlogModerList', 'BlogModer',
           'BlogBannedList', 'BlogBanned')


class BlogList(BaseView):
    @json_response
    async def get(self):
        return await m.Blog.select(self.request.conn, 0, self.request.uid)


class Blog(BaseView):
    @json_response
    async def get(self):
        return await m.Blog.id_u(self.request)

    @json_response
    @v.get_body(v.blogs.update)
    async def patch(self, body):
        await (await m.Blog.id_u(self.request)).update(body)


class BlogHistory(BaseView):
    @json_response
    async def get(self):
        return await (await m.Blog.id_u(self.request)).history()


class BlogModerList(BaseView):
    @json_response
    async def get(self):
        return await (await m.Blog.id_u(self.request)).moders_select()

    @json_response
    @v.get_body(v.blogs.moders_insert)
    async def post(self, body):
        ids = await (await m.Blog.id_u(self.request)).moders_insert(body)
        loc = '/blogs/%i/moders/%i' % ids

        return {'Location': loc}, 201, {'Location': loc}


class BlogModer(BaseView):
    @json_response
    async def get(self):
        return await (await m.Blog.id_u(self.request)).moders_id_u(
            self.request)

    @json_response
    @v.get_body(v.blogs.moders_update)
    async def patch(self, body):
        await (await (await m.Blog.id_u(self.request)).moders_id_u(
            self.request)).update(body)

    @json_response
    async def delete(self):
        await (await (await m.Blog.id_u(self.request)).moders_id_u(
            self.request)).delete()


class BlogBannedList(BaseView):
    @json_response
    async def get(self):
        return await (await m.Blog.id_u(self.request)).bans_select()

    @json_response
    @v.get_body(v.blogs.bans_insert)
    async def post(self, body):
        ids = await (await m.Blog.id_u(self.request)).bans_insert(body)
        loc = '/blogs/%i/bans/%i' % ids

        return {'Location': loc}, 201, {'Location': loc}


class BlogBanned(BaseView):
    @json_response
    async def get(self):
        return await (await m.Blog.id_u(self.request)).bans_id_u(self.request)

    async def delete(self):
        await (await (await m.Blog.id_u(self.request)).bans_id_u(
            self.request)).delete()

