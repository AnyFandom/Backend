#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m, postgres
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('BlogList', 'Blog', 'BlogHistory',
           'BlogModerList', 'BlogModer',
           'BlogBannedList', 'BlogBanned',
           'BlogPostList', 'BlogCommentList')


class BlogList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await m.Blog.select(self.request.conn, self.request.uid, 0)


class Blog(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await m.Blog.id_u(self.request)

    @json_response
    @v.get_body(v.blogs.update)
    @postgres
    async def patch(self, body):
        await (await m.Blog.id_u(self.request)).update(body)


class BlogHistory(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Blog.id_u(self.request)).history()


class BlogModerList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Blog.id_u(self.request)).moders_select()

    @json_response
    @v.get_body(v.blogs.moders_insert)
    @postgres
    async def post(self, body):
        ids = await (await m.Blog.id_u(self.request)).moders_insert(body)
        loc = f'/blogs/{ids[0]}/moders/{ids[1]}'

        return {'Location': loc}, 201, {'Location': loc}


class BlogModer(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Blog.id_u(self.request)).moders_id_u(
            self.request)

    @json_response
    @v.get_body(v.blogs.moders_update)
    @postgres
    async def patch(self, body):
        await (await (await m.Blog.id_u(self.request)).moders_id_u(
            self.request)).update(body)

    @json_response
    @postgres
    async def delete(self):
        await (await (await m.Blog.id_u(self.request)).moders_id_u(
            self.request)).delete()


class BlogBannedList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Blog.id_u(self.request)).bans_select()

    @json_response
    @v.get_body(v.blogs.bans_insert)
    @postgres
    async def post(self, body):
        ids = await (await m.Blog.id_u(self.request)).bans_insert(body)
        loc = f'/blogs/{ids[0]}/bans/{ids[1]}'

        return {'Location': loc}, 201, {'Location': loc}


class BlogBanned(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Blog.id_u(self.request)).bans_id_u(self.request)

    async def delete(self):
        await (await (await m.Blog.id_u(self.request)).bans_id_u(
            self.request)).delete()


class BlogPostList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Blog.id_u(self.request)).posts_select()

    @json_response
    @v.get_body(v.posts.insert)
    @postgres
    async def post(self, body):
        new_id = await (await m.Blog.id_u(self.request)).posts_insert(body)
        loc = f'/posts/{new_id}'

        return {'Location': loc}, 201, {'Location': loc}


class BlogCommentList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Blog.id_u(self.request)).comments_select()
