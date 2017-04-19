#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.web import JsonResponse

__all__ = ('clear_db',)


async def clear_db(request):
    async with request.app['db'].acquire() as conn:
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "AND table_name != 'migro_ver'")
        sql = 'TRUNCATE ' + ', '.join(x['table_name'] for x in tables)
        await conn.execute(sql)

    return JsonResponse(sql)
