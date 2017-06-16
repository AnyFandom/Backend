#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, JsonResponse, validators as v

__all__ = ('BlogList', 'Blog')


class BlogList(BaseView):
    async def get(self):
        return JsonResponse(
            await m.Blog.select(self.request.conn, 0, self.request.uid))


class Blog(BaseView):
    async def get(self):
        return JsonResponse(await m.Blog.id_u(self.request))

    async def patch(self):
        body = await v.get_body(self.request, v.blogs.update)
        await (await m.Blog.id_u(self.request)).update(body)

        return JsonResponse()


class BlogHistory(BaseView):
    async def get(self):
        return JsonResponse(await (await m.Blog.id_u(self.request)).history())

