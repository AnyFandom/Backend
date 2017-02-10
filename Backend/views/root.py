#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils import web


class RootView(web.BaseView):
    async def get(self):
        return web.JsonResponse({'it': 'works'})
