#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest


@pytest.fixture(scope='module')
def url(request):
    return 'http://localhost:8080'


@pytest.fixture(scope='module')
def conf(request):
    return dict(
        username='TestUser',
        password='123454321',
        new_password='123456789'
    )
