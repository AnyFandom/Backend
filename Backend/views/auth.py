#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

from ..utils import db
from ..utils.web import json_response
from ..utils.web import validators as v
from ..utils.web.tkn import encode_timed, decode_timed
from ..utils.web.exceptions import NotYetImplemented, InvalidToken

__all__ = ('register', 'login', 'refresh', 'invalidate', 'change', 'reset')


@json_response
@v.get_body(v.auth.register)
@db.postgres
async def register(request, body):
    """Регистрация нового пользователя"""
    new_id = await db.auth.register(
        request.conn, body['username'], body['password']
    )
    loc = f'/users/{new_id}'

    return {'Location': loc}, 201, {'Location': loc}


@json_response
@v.get_body(v.auth.login)
@db.postgres
async def login(request, body):
    """Получение токенов по логину/паролю"""
    user_id, rand = await db.auth.login(
        request.conn, body['username'], body['password']
    )

    access_token = encode_timed(
        'I4s', user_id, socket.inet_aton(request.headers['X-Real-IP']),
        key=request.app['cfg']['access_key'], life=600
    ).decode('utf-8')

    refresh_token = encode_timed(
        'I16s', user_id, rand.bytes, life=2419200,
        key=request.app['cfg']['refresh_key']
    ).decode('utf-8')

    return dict(access_token=access_token, refresh_token=refresh_token)


@json_response
@v.get_body(v.auth.refresh)
@db.postgres
async def refresh(request, body):
    """Получение нового access токена по refresh токену"""
    decoded = decode_timed(
        body['refresh_token'].encode('utf-8'),
        key=request.app['cfg']['refresh_key']
    )

    if await db.auth.check_random(request.conn, decoded[0], decoded[1]):
        access_token = encode_timed(
            'I4s', decoded[0], socket.inet_aton(request.headers['X-Real-IP']),
            key=request.app['cfg']['access_key'], life=600
        ).decode('utf-8')

        return dict(access_token=access_token)
    else:
        raise InvalidToken


@json_response
@v.get_body(v.auth.invalidate)
@db.postgres
async def invalidate(request, body):
    """Анулировать все refresh токены (access токены все еще действуют)"""
    await db.auth.invalidate(
        request.conn, body['username'], body['password']
    )


@json_response
@v.get_body(v.auth.change)
@db.postgres
async def change(request, body):
    """Сменить пароль"""
    await db.auth.change(
        request.conn, body['username'], body['password'], body['new_password']
    )


async def reset(request, body):
    raise NotYetImplemented
