#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import base64

import jwt

from ..utils import db
from ..utils.web import JsonResponse
from ..utils.web import validators as v
from ..utils.web.exceptions import (InvalidRefresh, ExpiredRefresh,
                                    NotYetImplemented)
from ..utils.web.other import hash_host


async def register(request):
    """Регистрация нового пользователя"""
    body = await v.get_body(request, v.auth.register)
    new_id = await db.auth.register(
        request.conn, body['username'], body['password']
    )

    return JsonResponse(
        {'Location': '/users/%i' % new_id}, status_code=201,
        headers={'Location': '/users/%i' % new_id}
    )


async def login(request):
    """Получение токенов по логину/паролю"""
    body = await v.get_body(request, v.auth.login)
    i, r = await db.auth.login(
        request.conn, body['username'], body['password']
    )

    t = int(time.time())

    return JsonResponse({
        'refresh_token': jwt.encode({
            'id': i, 'random': r, 'exp': t + 2419200  # 28 дней
        }, key=request.app['cfg']['refresh_key']).decode(),
        'access_token': jwt.encode({
            'id': i, 'exp': t + 600,  # 10 минут
            'for': base64.b64encode(hash_host(request)).decode('utf-8')
        }, key=request.app['cfg']['access_key']).decode()
    })


async def refresh(request):
    """Получение нового access токена по refresh токену"""
    body = await v.get_body(request, v.auth.refresh)

    try:
        decoded = jwt.decode(
            body['refresh_token'], key=request.app['cfg']['refresh_key']
        )
    except jwt.DecodeError:
        raise InvalidRefresh
    except jwt.ExpiredSignatureError:
        raise ExpiredRefresh

    if await db.auth.check_random(
            request.conn, decoded['id'], decoded['random']
    ):
        return JsonResponse({
            'access_token': jwt.encode({
                'id': decoded['id'], 'exp': int(time.time()) + 600,
                'for': base64.b64encode(hash_host(request)).decode('utf-8')
            }, key=request.app['cfg']['access_key']).decode()
        })
    else:
        raise InvalidRefresh


async def invalidate(request):
    """Анулировать все refresh токены (access токены все еще действуют)"""
    body = await v.get_body(request, v.auth.invalidate)
    await db.auth.invalidate(
        request.conn, body['username'], body['password']
    )
    return JsonResponse()


async def change(request):
    """Сменить пароль"""
    body = await v.get_body(request, v.auth.change)
    await db.auth.change(
        request.conn, body['username'], body['password'], body['new_password']
    )
    return JsonResponse()


async def reset(request):
    raise NotYetImplemented
