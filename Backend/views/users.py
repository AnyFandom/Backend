#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, JsonResponse, validators as v

__all__ = ('UserList', 'User', 'UserHistory')


class UserList(BaseView):
    async def get(self):
        return JsonResponse(
            await m.User.select(self.request.conn, self.request.uid))


class User(BaseView):
    async def get(self):
        return JsonResponse(await m.User.id_u(self.request))

    async def patch(self):
        body = await v.get_body(self.request, v.users.update)
        await (await m.User.id_u(self.request)).update(body)

        return JsonResponse()


class UserHistory(BaseView):
    async def get(self):
        return JsonResponse(await (await m.User.id_u(self.request)).history())
