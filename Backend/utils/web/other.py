#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hmac
import hashlib


def hash_host(request) -> bytes:
    """Выдирает hostname из request и хэширует его"""
    # Когда будем пихать бэкенд под Nginx, надо поменять
    peername = request.headers['X-Real-IP']
    if peername is not None:
        host = peername[0]
    else:  # На всякий случай
        raise Exception('idk what happend')

    digest = hmac.new(
        request.app['cfg']['ip_key'].encode(),
        host.encode(), hashlib.sha1
    ).digest()

    return digest
