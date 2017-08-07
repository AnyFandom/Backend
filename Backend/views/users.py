#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('UserList', 'User', 'UserHistory', 'UserBlogList', 'UserPostList',
           'UserCommentList')


class UserList(BaseView):
    @json_response
    @v.get_query(v.base.page)
    async def get(self, query):
        return await m.User.select(
            self.request.conn, self.request.uid, page=query['page'])


class User(BaseView):
    @json_response
    async def get(self):
        return await m.User.id_u(self.request)

    @json_response
    @v.get_body(v.users.update)
    async def patch(self, body):
        await (await m.User.id_u(self.request)).update(body)


class UserHistory(BaseView):
    @json_response
    async def get(self):
        return await (await m.User.id_u(self.request)).history()


class UserBlogList(BaseView):
    @json_response
    async def get(self):
        return await (await m.User.id_u(self.request)).blogs()


class UserPostList(BaseView):
    @json_response
    async def get(self):
        return await (await m.User.id_u(self.request)).posts()


class UserCommentList(BaseView):
    @json_response
    async def get(self):
        return await (await m.User.id_u(self.request)).comments()
