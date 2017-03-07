#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import add_user
from ..utils.web import JsonResponse, get_body
from ..utils.web.validators import register_validator


async def register(request):
    body = await get_body(request, register_validator)

    new_id = await add_user(request.conn, body['username'], body['password'])

    return JsonResponse({'Location': '/users/%i' % new_id}, status_code=201,
                        headers={'Location': '/users/%i' % new_id})
