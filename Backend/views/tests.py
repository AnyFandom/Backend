#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import db
from ..utils.web import json_response

__all__ = ('clear_db', 'execute', 'logout')


@json_response
@db.postgres
async def clear_db(request):
    tables = await request.conn.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
        "AND table_name != 'migro_ver'")
    sql = 'TRUNCATE ' + ', '.join(x['table_name'] for x in tables)
    await request.conn.execute(sql)

    return dict(sql=sql)


@json_response
@db.postgres
async def execute(request):
    sql = (await request.json())['sql']
    await request.conn.execute(sql)

    return dict(sql=sql)

