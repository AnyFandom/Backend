#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils import db
from ..utils.web import BaseView, JsonResponse
from ..utils.web.exceptions import UserDoesNotExists, NotYetImplemented


class UserListView(BaseView):
    async def get(self):
        return JsonResponse(await db.users.get_users(self.request.conn))


class UserView(BaseView):
    async def get(self):
        try:
            if self.request.match_info['first'] == 'current':
                raise NotYetImplemented  # TODO
            elif (self.request.match_info['first'] == 'u' and
                  'second' in self.request.match_info):
                resp = (await db.users.get_users(
                    self.request.conn, self.request.match_info['second'],
                    u=True
                ))[0]
            else:
                resp = (await db.users.get_users(
                    self.request.conn, self.request.match_info['first']
                ))[0]
        except (IndexError, ValueError):
            raise UserDoesNotExists

        return JsonResponse(resp)
