#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.web import BaseView, JsonResponse

__all__ = ('Root',)


class Root(BaseView):
    async def get(self):
        return JsonResponse({'it': 'works!'})
