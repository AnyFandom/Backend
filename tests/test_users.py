#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import requests

user_id = ''
access_token = ''


class TestUsers:
    def test_init(self, url, conf):
        global user_id, access_token

        r = requests.post(url+'/clear_db')
        if r.status_code != 200:
            pytest.exit('Server must be running in test mode')

        options = dict(
            username=conf['username'],
            password=conf['password']
        )

        user_id = requests.post(
            url+'/auth/register', json=options).json()['data']['Location'][7:]
        access_token = requests.post(
            url+'/auth/login', json=options).json()['data']['access_token']

    # --- USERS GET --- #

    def test_users_get(self, url):
        r = requests.get(url+'/users')
        assert r.status_code == 200

    def test_users_get_with_wrong_id(self, url):
        r = requests.get(url+'/users/0')
        assert r.status_code == 404

    def test_users_get_with_wrong_username(self, url):
        r = requests.get(url+'/users/u/0')
        assert r.status_code == 404

    def test_users_get_current_without_token(self, url):
        r = requests.get(url+'/users/current')
        assert r.status_code == 403

    def test_users_get_with_id(self, url):
        global user_id
        r = requests.get(url+'/users/'+user_id)
        assert r.status_code == 200

    def test_users_get_with_username(self, url, conf):
        r = requests.get(url+'/users/u/'+conf['username'])
        assert r.status_code == 200

    def test_users_get_current(self, url):
        global access_token
        r = requests.get(url+'/users/current', headers=dict(
            Authorization='Token '+access_token))
        assert r.status_code == 200

    # --- USERS PATCH --- #

    def test_users_patch_by_id_without_token(self, url):
        global user_id
        r = requests.patch(url+'/users/'+user_id, json=dict())
        assert r.status_code == 403

    def test_users_patch_by_username_without_token(self, url, conf):
        r = requests.patch(url+'/users/u/'+conf['username'], json=dict())
        assert r.status_code == 403

    def test_users_patch_by_id(self, url):
        global user_id, access_token
        r = requests.patch(
            url+'/users/'+user_id, json=dict(), headers=dict(
                Authorization='Token '+access_token))
        assert r.status_code == 200

    def test_users_patch_by_username(self, url, conf):
        global access_token
        r = requests.patch(
            url+'/users/u/'+conf['username'], json=dict(), headers=dict(
                Authorization='Token '+access_token))
        assert r.status_code == 200

    # --- USERS HISTORY GET --- #

    def test_users_history_get_by_id_without_token(self, url):
        global user_id
        r = requests.get(url+'/users/'+user_id+'/history')
        assert r.status_code == 403

    def test_users_history_get_username_id_without_token(self, url, conf):
        r = requests.get(url+'/users/u/'+conf['username']+'/history')
        assert r.status_code == 403

    def test_users_history_get_by_id(self, url):
        global user_id, access_token
        r = requests.get(
            url+'/users/'+user_id+'/history', headers=dict(
                Authorization='Token ' + access_token))
        assert r.status_code == 200

    def test_users_history_get_by_username(self, url, conf):
        global access_token
        r = requests.get(
            url+'/users/u/'+conf['username']+'/history', headers=dict(
                Authorization='Token ' + access_token))
        assert r.status_code == 200
