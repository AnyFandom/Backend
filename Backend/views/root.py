#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils import web


class RootView(web.BaseView):
    async def get(self):
        resp = await self.request.conn.fetchrow(
            "SELECT 'testing testing 123' AS test")

        return web.JsonResponse({'test': resp['test']})
