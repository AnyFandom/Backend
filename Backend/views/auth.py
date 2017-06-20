#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

from ..utils import db
from ..utils.web import JsonResponse
from ..utils.web import validators as v
from ..utils.web.tkn import encode_timed, decode_timed
from ..utils.web.exceptions import NotYetImplemented, InvalidToken

__all__ = ('register', 'login', 'refresh', 'invalidate', 'change', 'reset')


@v.get_body(v.auth.register)
async def register(request, body):
    """Регистрация нового пользователя"""
    new_id = await db.auth.register(
        request.conn, body['username'], body['password']
    )

    return JsonResponse(
        {'Location': '/users/%i' % new_id}, status_code=201,
        headers={'Location': '/users/%i' % new_id}
    )


@v.get_body(v.auth.login)
async def login(request, body):
    """Получение токенов по логину/паролю"""
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


@v.get_body(v.auth.refresh)
async def refresh(request, body):
    """Получение нового access токена по refresh токену"""
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


@v.get_body(v.auth.invalidate)
async def invalidate(request, body):
    """Анулировать все refresh токены (access токены все еще действуют)"""
    await db.auth.invalidate(
        request.conn, body['username'], body['password']
    )
    return JsonResponse()


@v.get_body(v.auth.change)
async def change(request, body):
    """Сменить пароль"""
    await db.auth.change(
        request.conn, body['username'], body['password'], body['new_password']
    )
    return JsonResponse()


async def reset(request, body):
    raise NotYetImplemented
