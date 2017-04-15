#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

from ..utils import db
from ..utils.web import JsonResponse
from ..utils.web import validators as v
from ..utils.web.tkn import encode_timed, decode_timed
from ..utils.web.exceptions import NotYetImplemented, InvalidToken

__all__ = ('register', 'login', 'refresh', 'invalidate', 'change', 'reset')


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
    user_id, rand = await db.auth.login(
        request.conn, body['username'], body['password']
    )

    return JsonResponse(dict(
        access_token=encode_timed(
            'I4s', user_id, socket.inet_aton(request.headers['X-Real-IP']),
            key=request.app['cfg']['access_key'], life=600
        ).decode('utf-8'),
        refresh_token=encode_timed(
            'I16s', user_id, rand.bytes, life=2419200,
            key=request.app['cfg']['refresh_key']
        ).decode('utf-8')
    ))


async def refresh(request):
    """Получение нового access токена по refresh токену"""
    body = await v.get_body(request, v.auth.refresh)

    decoded = decode_timed(
        body['refresh_token'].encode('utf-8'),
        key=request.app['cfg']['refresh_key']
    )

    if await db.auth.check_random(request.conn, decoded[0], decoded[1]):
        return JsonResponse(dict(
            access_token=encode_timed(
                'I4s', decoded[0],
                socket.inet_aton(request.headers['X-Real-IP']),
                key=request.app['cfg']['access_key'], life=600
            ).decode('utf-8')
        ))
    else:
        raise InvalidToken


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
