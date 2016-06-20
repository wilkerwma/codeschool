#!/usr/bin/env python
import os
import sys
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codeschool.settings")
django.setup()

from cs_questions.models import *
from cs_core.models import *
from pprint import pprint
from collections import OrderedDict
import json

def transform(x):
    y = x.copy()
    try:
        result = {k: v for (k, v) in x.pop('fields').items() if (v is not None and v != '')}
        pk = x.pop('pk', None)
        if pk:
            result['id'] = pk
        result['model/type'] = x.pop('model')
        if x:
            raise ValueError(x)
    except:
        print(y)
        raise
    return result

def group(db):
    result = OrderedDict()
    for x in db:
        try:
            tt = x['model/type']
            result[tt].append(x)
        except KeyError:
            result[tt] = [x]
    return result

def select(db, values):
    instances = []
    for section in values:
        print('model: %s, size: %s' % (section, len(db[section])))
        instances.extend(db[section])
    return instances
        
def select_at(db, values, path): 
    save_at(select(db, values), path)

def save(x, path):
    with open(path, 'w') as F:
        json.dump(x, F, indent=2)
        print('saved %s elements' % len(x))
              
def fused(db):
    data = OrderedDict()
    for x in db:
        y = data.setdefault(x['id'], {}) 
        y.update(x)
        y['N'] = y.get('N', 0) + 1
    data = [x for x in data.values() if x['N'] > 1]
    [x.pop('N') for x in data]
    return data
    
db = json.load(open('db.json'))
db = [transform(x) for x in db]
db = group(db)

#
# Questions
#
def load_questions():
    io = select(db, ['cs_questions.question', 'cs_questions.codingioquestion'])
    io = fused(io)
    ak = select(db, ['cs_questions.codingioanswerkey'])
    save(io + ak, 'io.json')

    Q = select(db, ['cs_questions.question', 'cs_questions.numericquestion'])
    Q = fused(Q)
    save(Q, 'Q.json')

#
# Users
#
def load_users():
    select_at(db, ['auth.user', 'cs_auth.profile'], 'users.json')
    

#
# Load responses
#
def load_resp():
    x = select(db, ['cs_activities.response', 'cs_questions.codingioresponse'])
    resp = fused(x)
    x = select(db, ['cs_activities.response', 'cs_questions.numericresponse'])
    resp += fused(x)
    x = select(db, ['cs_activities.response', 'cs_questions.quizresponse'])
    resp += fused(x)
    save(resp, 'resp.json')

