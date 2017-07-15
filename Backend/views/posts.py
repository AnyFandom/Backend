#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('PostList', 'Post', 'PostHistory')


class PostList(BaseView):
    @json_response
    async def get(self):
        return await m.Post.select(self.request.conn, 0, 0, self.request.uid)


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
