#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('CommentList', 'Comment', 'CommentHistory', 'CommentVoteList')


class CommentList(BaseView):
    @json_response
    async def get(self):
        return await m.Comment.select(
            self.request.conn, self.request.uid, 0, 0, 0)


class Comment(BaseView):
    @json_response
    async def get(self):
        return await m.Comment.id_u(self.request)

    @json_response
    @v.get_body(v.comments.update)
    async def patch(self, body):
        await (await m.Comment.id_u(self.request)).update(body)


class CommentHistory(BaseView):
    @json_response
    async def get(self):
        return await (await m.Comment.id_u(self.request)).history()


class CommentVoteList(BaseView):
    @json_response
    async def get(self):
        return await (await m.Comment.id_u(self.request)).votes_select()

    @json_response
    @v.get_body(v.comments.votes_insert)
    async def post(self, body):
        await (await m.Comment.id_u(self.request)).votes_insert(body)

        return None, 201
