#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.web import BaseView, JsonResponse


class RootView(BaseView):
    async def get(self):
        return JsonResponse({'it': 'works!'})
