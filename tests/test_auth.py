#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests


refresh_token = ''
access_token = ''


class TestAuth:
    # --- REGISTER --- #

    def test_register_without_anything(self, url):
        r = requests.post(url+'/auth/register', json=dict())
        assert r.status_code == 400

    def test_register_without_username(self, url, conf):
        options = dict(
            password=conf['password']
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 400

    def test_register_without_password(self, url, conf):
        options = dict(
            username=conf['username']
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 400

    def test_register_with_short_everything(self, url):
        options = dict(
            username='',
            password='',
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 400

    def test_register_with_short_username(self, url, conf):
        options = dict(
            username='',
            password=conf['password']
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 400

    def test_register_with_short_password(self, url, conf):
        options = dict(
            username=conf['username']
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 400

    def test_register_with_long_everything(self, url):
        options = dict(
            username='D'*65,
            password='D'*257
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 400

    def test_register_with_long_username(self, url, conf):
        options = dict(
            username='D'*65,
            password=conf['password']
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 400

    def test_register_with_long_password(self, url, conf):
        options = dict(
            username=conf['username'],
            password='D'*257
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 400

    def test_register(self, url, conf):
        options = dict(
            username=conf['username'],
            password=conf['password']
        )
        r = requests.post(url+'/auth/register', json=options)
        assert r.status_code == 201

    def test_register_with_same_username(self, url, conf):
        options = dict(
            username=conf['username'],
            password=conf['password']
        )
        r = requests.post(url + '/auth/register', json=options)
        assert r.status_code == 409

    # --- LOGIN --- #

    def test_login_without_everything(self, url):
        r = requests.post(url+'/auth/login', json=dict())
        assert r.status_code == 400

    def test_login_without_username(self, url, conf):
        options = dict(
            password=conf['password']
        )
        r = requests.post(url+'/auth/login', json=options)
        assert r.status_code == 400

    def test_login_without_password(self, url, conf):
        options = dict(
            username=conf['username']
        )
        r = requests.post(url+'/auth/login', json=options)
        assert r.status_code == 400

    def test_login_with_wrong_everything(self, url):
        options = dict(
            username='',
            password=''
        )
        r = requests.post(url+'/auth/login', json=options)
        assert r.status_code == 400

    def test_login_with_wrong_username(self, url, conf):
        options = dict(
            username='',
            password=conf['password']
        )
        r = requests.post(url+'/auth/login', json=options)
        assert r.status_code == 400

    def test_login_with_wrong_password(self, url, conf):
        options = dict(
            username=conf['username'],
            password=''
        )
        r = requests.post(url+'/auth/login', json=options)
        assert r.status_code == 400

    def test_login(self, url, conf):
        global access_token, refresh_token
        options = dict(
            username=conf['username'],
            password=conf['password']
        )
        r = requests.post(url+'/auth/login', json=options)
        assert r.status_code == 200
        body = r.json()

        access_token = body['data']['access_token']
        refresh_token = body['data']['refresh_token']

    # --- REFRESH --- #

    def test_refresh_without_token(self, url):
        r = requests.post(url+'/auth/refresh', json=dict())
        assert r.status_code == 400

    def test_refresh_with_invalid_token(self, url):
        options = dict(
            refresh_token=''
        )
        r = requests.post(url+'/auth/refresh', json=options)
        assert r.status_code == 400

    # TODO: Добавить тесты для истекшего токена

    def test_refresh(self, url):
        global access_token, refresh_token
        options = dict(
            refresh_token=refresh_token
        )
        r = requests.post(url+'/auth/refresh', json=options)
        assert r.status_code == 200
        body = r.json()

        access_token = body['data']['access_token']

    # --- INVALIDATE --- #

    # Правильность введенных данных проверяется точно так же как и в
    # /auth/login, так что это можно пропустить

    def test_invalidate(self, url, conf):
        options = dict(
            username=conf['username'],
            password=conf['password']
        )
        r = requests.post(url+'/auth/invalidate', json=options)
        assert r.status_code == 200

        # Снова логинимся
        self.test_login(url, conf)

    # --- CHANGE --- #

    def test_change_without_everything(self, url):
        r = requests.post(url+'/auth/change', json=dict())
        assert r.status_code == 400

    def test_change_without_username(self, url, conf):
        options = dict(
            password=conf['password'],
            new_password=conf['new_password']
        )
        r = requests.post(url+'/auth/change', json=options)
        assert r.status_code == 400

    def test_change_without_password(self, url, conf):
        options = dict(
            username=conf['username'],
            new_password=conf['new_password']
        )
        r = requests.post(url+'/auth/change', json=options)
        assert r.status_code == 400

    def test_change_without_new_password(self, url, conf):
        options = dict(
            username=conf['username'],
            password=conf['password']
        )
        r = requests.post(url+'/auth/change', json=options)
        assert r.status_code == 400

    # Правильность комбинации username/password проверяется точно
    # так же как и в /auth/login, так что это можно пропустить

    def test_change_with_short_new_password(self, url, conf):
        options = dict(
            username=conf['username'],
            password=conf['password'],
            new_password=''
        )
        r = requests.post(url+'/auth/change', json=options)
        assert r.status_code == 400

    def test_change_with_long_new_password(self, url, conf):
        options = dict(
            username=conf['username'],
            password=conf['password'],
            new_password='D'*257
        )
        r = requests.post(url+'/auth/change', json=options)
        assert r.status_code == 400

    def test_change(self, url, conf):
        options = dict(
            username=conf['username'],
            password=conf['password'],
            new_password=conf['new_password']
        )
        r = requests.post(url+'/auth/change', json=options)
        assert r.status_code == 200

    def test_login_with_old_password(self, url, conf):
        options = dict(
            username=conf['username'],
            password=conf['password']
        )
        r = requests.post(url+'/auth/login', json=options)
        assert r.status_code == 400

    def test_login_with_new_password(self, url, conf):
        global access_token, refresh_token
        options = dict(
            username=conf['username'],
            password=conf['new_password']
        )
        r = requests.post(url+'/auth/login', json=options)
        assert r.status_code == 200
        body = r.json()

        access_token = body['data']['access_token']
        refresh_token = body['data']['refresh_token']
