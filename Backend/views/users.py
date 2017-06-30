#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('UserList', 'User', 'UserHistory')


class UserList(BaseView):
    @json_response
    async def get(self):
        return await m.User.select(self.request.conn, self.request.uid)


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
