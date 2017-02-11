#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils import web


class RootView(web.BaseView):
    async def get(self):
        conn = await self.request.app['db'].acquire()

        resp = await conn.fetchrow("SELECT 'testing testing 123' AS test")

        await self.request.app['db'].release(conn)

        return web.JsonResponse({'test': resp['test']})
