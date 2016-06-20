#!/usr/bin/env python
import os
import sys
import django
from pprint import pprint
import json
from django.db import transaction
from markdown import markdown
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codeschool.settings")
django.setup()

from codeschool.models import User
from cs_questions.models import CodingIoQuestion, FormQuestion, AnswerKeyItem, programming_language, CodingIoResponseItem, FormResponseItem, Quiz, QuizResponseItem
from cs_core.models import Course

def strip(x, *args):
    del x['model/type']
    for k in args:
        x.pop(k, None)
    return x.pop('id', None)

# Base page
base = Course.objects.first().questions_page
idmap = {}

def qids():
    with open('qid.json', 'r') as F:
        return {int(k): v for k, v in json.load(F).items()}

def rids():
    with open('rid.json', 'r') as F:
        return {int(k): v for k, v in json.load(F).items()}


#
# Convert numeric questions
#
def convert_form():
    print('converting numeric questions')
    FormQuestion.objects.delete()
    with open('qid.json', 'r') as F:
        idmap.update({int(k): v for k, v in json.load(F).items()})

    with transaction.atomic():
        for x in json.load(open('Q.json')):
            if 'numericquestion' in x['model/type']:
                id = strip(x, 'modified', 'created', 'is_active', 'discipline', 'owner',
                              'status', 'status_changed', 'author_name',)
                x['stem'] = json.dumps([{'value': x.pop('long_description'), 'type': 'markdown'}]) 
                x['body'] = json.dumps([
                    {
                        'type': 'numeric',
                        'value': {
                             'name': 'Resposta',
                             'tolerance': str(x.pop('tolerance')),
                             'answer': str(x.pop('answer')),
                             'value': 1.0,
                         }, 
                     },
                ])
                q = FormQuestion.objects.create(parent_page=base, **x)
                print(q)
                idmap[int(id)] = q.id
    
    with open('qid.json', 'w') as F:
        json.dump(idmap, F, indent=2)


#
# Convert io questions
#
def convert_io():
    print('converting io questions')
    
    CodingIoQuestion.objects.delete()
    with open('qid.json', 'r') as F:
        idmap.update({int(k): v for k, v in json.load(F).items()})

    with transaction.atomic():
        for x in json.load(open('io.json')):
            if 'codingioquestion' in x['model/type']:
                id = strip(x, 'modified', 'created', 'is_active', 'discipline', 'owner',
                              'status', 'status_changed', 'author_name',)
                x['stem'] = json.dumps([{'value': x.pop('long_description'), 'type': 'markdown'}]) 
                q = CodingIoQuestion.objects.create(parent_page=base, **x)
                print(q)
                idmap[int(id)] = q.id

    with open('qid.json', 'w') as F:
        json.dump(idmap, F, indent=2)

    # Convert answer keys
    def answer_keys():
        with open('qid.json', 'r') as F:
                idmap.update({int(k): v for k, v in json.load(F).items()})

        with transaction.atomic():
            for x in json.load(open('io.json')):
                if x['model/type'] == 'cs_questions.codingioanswerkey':
                    id = strip(x, 'iospec_hash', 'is_valid')
                    x['question'] = CodingIoQuestion.objects.get(pk=idmap[x['question']])
                    x['language'] = programming_language(x['language'])
                    ak = AnswerKeyItem.objects.create(**x)
                    print(ak)
    answer_keys()
                

#
# Responses
#
def convert_resps():
    # CodingIoResponseItem.objects.all().delete()
    quiz = Quiz.objects.first()
    print('converting responses')
    qmap = qids()
    rmap = rids()

    def io(x, quiz=None):
        y = x.copy()
        question = CodingIoQuestion.objects.get(pk=qmap[x.pop('question_for_unbound')])
        kwargs = {} if quiz is None else {'context': quiz.default_context}
        try:
            resp = CodingIoResponseItem(
                language=programming_language(x.pop('language')),
                user=User.objects.get(username=x.pop('user')[0]),
                source=x.pop('source', None),
                created=x.pop('created'),
                question=question,
                **kwargs,
            )
            resp.full_clean()
            resp.autograde()
        except:
            print(question)
            pprint(y)
            raise
        strip(x, 'status', 'modified', 'given_grade', 'final_grade', 'feedback_data', 
              'manual_override', 'status_changed', 'is_converted', 'parent')
        if x:
            raise Exception(x)  
        
        print(resp)
        return resp
        
    def numeric(x, quiz=None):
        y = x.copy()
        question = FormQuestion.objects.get(pk=qmap[x.pop('question_for_unbound')])
        kwargs = {} if quiz is None else {'context': quiz.default_context}
        try:
            key = question.body[0].value['ref']
            resp = FormResponseItem(
                user=User.objects.get(username=x.pop('user')[0]),
                created=x.pop('created'),
                question=question,
                responses={key: x.pop('value', None)},
                **kwargs
            )
            resp.full_clean()
            resp.autograde()
            if quiz:
                quiz.process_response_item(resp)
        except:
            print(question)
            pprint(y)
            raise
        strip(x, 'status', 'modified', 'given_grade', 'final_grade', 'feedback_data', 
              'manual_override', 'status_changed', 'is_converted', 'parent')
        if x:
            raise Exception(x)  
        
        print(resp)
        return resp

    with transaction.atomic():
        for x in json.load(open('resp.json')):
            id = x['id']
            if 'quizresponse' in x['model/type']:
                continue
            elif 'question_for_unbound' in x and 'parent' not in x:
                if 'codingioresponse' in x['model/type'] and 'source' in x:
                    if id in rmap: continue
                    r = io(x)
                elif 'numericresponse' in x['model/type']:
                    if id in rmap: continue
                    r = numeric(x)
                else:
                    continue
            elif 'parent' in x:
                if 'codingioresponse' in x['model/type'] and 'source' in x:
                    #if id in rmap: continue
                    r = io(x, quiz)
                elif 'numeric' in x['model/type']:
                    if id in rmap: continue
                    r = numeric(x, quiz)
                else:
                    continue
            else:
                pprint(x)
                continue
            print('   graded: %s' % r.given_grade)
            rmap[id] = r.id
        #raise
        
    with open('rid.json', 'w') as F:
        json.dump(rmap, F, indent=2)
