#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.web.rewrites import BaseView
from ..utils.web.response import JsonResponse


class RootView(BaseView):
    async def get(self):
        resp = await self.request.conn.fetchrow(
            "SELECT 'testing testing 123' AS test")

        return JsonResponse({'test': resp['test']})
