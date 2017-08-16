#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..utils.db import models as m, postgres
from ..utils.web import BaseView, json_response, validators as v

__all__ = ('CommentList', 'Comment', 'CommentAnswers', 'CommentHistory',
           'CommentVoteList')


class CommentList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await m.Comment.select(
            self.request.conn, self.request.uid, 0, 0, 0)


class Comment(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await m.Comment.id_u(self.request)

    @json_response
    @v.get_body(v.comments.update)
    @postgres
    async def patch(self, body):
        await (await m.Comment.id_u(self.request)).update(body)


class CommentAnswers(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Comment.id_u(self.request)).answers()

    @json_response
    @v.get_body(v.comments.insert)
    @postgres
    async def post(self, body):
        new_id = await (await m.Comment.id_u(self.request)).insert_answer(body)
        loc = f'/comments/{new_id}'

        return {'Location': loc}, 201, {'Location': loc}


class CommentHistory(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Comment.id_u(self.request)).history()


class CommentVoteList(BaseView):
    @json_response
    @postgres
    async def get(self):
        return await (await m.Comment.id_u(self.request)).votes_select()

    @json_response
    @v.get_body(v.comments.votes_insert)
    @postgres
    async def post(self, body):
        await (await m.Comment.id_u(self.request)).votes_insert(body)

        return None, 201
