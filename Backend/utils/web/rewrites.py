#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from datetime import datetime
from collections import Sequence

from aiohttp import web, hdrs, web_urldispatcher
from multidict import CIMultiDict


class JsonResponse(web.Response):
    def __init__(self, body=None, status_code=None, headers=None, *,
                 status: str='success', **kwargs) -> None:
        if headers is None:
            headers = CIMultiDict()

        if status_code is None:
            status_code = 200

        kwargs.pop('content-type', None)
        headers[hdrs.CONTENT_TYPE] = 'application/json; charset=utf-8'

        body = Encoder(indent=4)(
            {'status': status, 'data': body}).encode('utf-8')

        super().__init__(body=body, status=status_code,
                         headers=headers, **kwargs)


from ..db.models.base import Obj, SelectResult  # noqa


def json_response(func):
    async def wrapped(*args, **kwargs):
        resp = await func(*args, **kwargs)

        if isinstance(resp, SelectResult):
            return JsonResponse(resp)
        elif isinstance(resp, Sequence):
            assert len(resp) <= 3, "Resp > 3"
            return JsonResponse(*resp)
        else:
            return JsonResponse(resp)
    return wrapped


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, Obj):
            return o._data
        super().default(o)

    def __call__(self, *args, **kwargs):
        return self.encode(*args, **kwargs)


from .exceptions import (ResourceNotFound, MethodNotAllowed,
                         ExpectationFailed)  # noqa


class Router(web_urldispatcher.UrlDispatcher):
    async def resolve(self, request):
        allowed_methods = set()

        for resource in self._resources:
            match_dict, allowed = await resource.resolve(request)
            if match_dict is not None:
                return match_dict
            else:
                allowed_methods |= allowed
        else:
            if allowed_methods:
                return web_urldispatcher.MatchInfoError(
                    MethodNotAllowed(allowed_methods))
            else:
                return web_urldispatcher.MatchInfoError(
                    ResourceNotFound())

    def add_route(self, method, path, handler,
                  *, name=None, expect_handler=None):
        resource = self.add_resource(path, name=name)
        return resource.add_route(method, handler,
                                  expect_handler=_expect_handler)

async def _expect_handler(request):
    expect = request.headers.get(hdrs.EXPECT)
    if request.version == web_urldispatcher.HttpVersion11:
        if expect.lower() == "100-continue":
            request.transport.write(b"HTTP/1.1 100 Continue\r\n\r\n")
        else:
            return ExpectationFailed(expect)


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
