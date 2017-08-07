#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('PostList', 'Post', 'PostHistory', 'PostVoteList',
           'PostCommentList')


class PostList(BaseView):
    @json_response
    async def get(self):
        return await m.Post.select(self.request.conn, self.request.uid, 0, 0)


class Post(BaseView):
    @json_response
    async def get(self):
        return await m.Post.id_u(self.request)

    @json_response
    @v.get_body(v.posts.update)
    async def patch(self, body):
        await (await m.Post.id_u(self.request)).update(body)


class PostHistory(BaseView):
    @json_response
    async def get(self):
        return await (await m.Post.id_u(self.request)).history()


class PostVoteList(BaseView):
    @json_response
    async def get(self):
        return await (await m.Post.id_u(self.request)).votes_select()

    @json_response
    @v.get_body(v.posts.votes_insert)
    async def post(self, body):
        await (await m.Post.id_u(self.request)).votes_insert(body)

        return None, 201


class PostCommentList(BaseView):
    @json_response
    async def get(self):
        return await (await m.Post.id_u(self.request)).comments_select()

    @json_response
    @v.get_body(v.comments.insert)
    async def post(self, body):
        new_id = await (await m.Post.id_u(self.request)).comments_insert(body)
        loc = f'/comments/{new_id}'

        return {'Location': loc}, 201, {'Location': loc}
