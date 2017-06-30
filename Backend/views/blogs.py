#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('BlogList', 'Blog', 'BlogHistory')


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

