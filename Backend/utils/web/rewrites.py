#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from aiohttp import web, hdrs
from multidict import CIMultiDict


class JsonResponse(web.Response):
    def __init__(self, body=None, status: str='success', *,
                 status_code=200, headers=None, **kwargs):
        if headers is None:
            headers = CIMultiDict()

        kwargs.pop('content-type', None)
        headers[hdrs.CONTENT_TYPE] = 'application/json; charset=utf-8'

        if body is not None:
            body = json.dumps({'status': status, 'data': body}).encode('utf-8')

        super().__init__(body=body, status=status_code,
                         headers=headers, **kwargs)


from .exceptions import MethodNotAllowed  # noqa


class BaseView(web.View):
    @property
    def _allowed_methods(self):
        return {m for m in hdrs.METH_ALL if hasattr(self, m.lower())}

    def _raise_allowed_methods(self):
        raise MethodNotAllowed(self._allowed_methods)

    async def head(self):
        return JsonResponse()

    async def options(self):
        return JsonResponse(
            headers={'Allow': ', '.join(sorted(self._allowed_methods))})
