#!/usr/bin/env python
import os
import sys
import django
import json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codeschool.settings")
django.setup()

from codeschool.models import User
from cs_core.models import Profile

def strip(x, *args):
    del x['model/type']
    for k in args:
        del x[k]
    return x.pop('id', None)

for x in json.load(open('users.json')):
    if x['model/type'] == 'auth.user':
        strip(x, 'user_permissions', 'groups')
        User.objects.get_or_create(**x)
    else:
        strip(x)
        username = x.pop('user')[0]
        if username == 'AnonymousUser':
            continue
        x['user'] = User.objects.get(username=username)
        Profile.objects.update_or_create(**x)
