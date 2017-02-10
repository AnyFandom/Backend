#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web


class RootView(web.View):
    async def get(self):
        return web.Response(text='It works!')
