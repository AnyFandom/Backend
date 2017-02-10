#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web, hdrs

from .response import JsonResponse
from .exceptions import MethodNotAllowed


class BaseView(web.View):
    @property
    def _allowed_methods(self):
        return {m for m in hdrs.METH_ALL if hasattr(self, m.lower())}

    def _raise_allowed_methods(self):
        raise MethodNotAllowed(', '.join(sorted(self._allowed_methods)))

    async def head(self):
        return JsonResponse()

    async def options(self):
        return JsonResponse(
            headers={'Allow': ', '.join(sorted(self._allowed_methods))})


