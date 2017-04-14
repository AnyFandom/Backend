#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.web import JsonResponse

__all__ = ('clear_db',)


async def clear_db(request):
    async with request.app['db'].acquire() as conn:
        await conn.execute(
            'TRUNCATE admins, auth, user_statics, user_versions, fandom_bans,'
            'fandom_moders, fandom_statics, fandom_versions'
        )

    return JsonResponse()
