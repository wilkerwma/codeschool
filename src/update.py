#!/usr/bin/env python
import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codeschool.settings")
import django
django.setup()

from cs_activities.models import Response as OldResponse
from cs_core.models import Course, Response, Discipline
from cs_questions.models import NumericResponse
from cs_questions.models import FormQuestion, CodingIoQuestion, AnswerKeyItem, Quiz, QuizItem, FormResponseItem, CodingIoResponseItem, QuizResponseItem
from cs_battles.models import BattleResponse

#[x.delete() for x in BattleResponse.objects.all()]
#[x.delete() for x in Response.objects.all()]
#[x.delete() for x in SimpleQuestionResponse.objects.all()]
#[x.delete() for x in CodingIoQuestion.objects.all()]
OldResponse.objects.all().update(is_converted=False)

Discipline.import_all(commit=True)
#Course.import_all(commit=True)

#SimpleQuestion.import_all(commit=True)
#CodingIoQuestion.import_all(commit=True)
#AnswerKeyItem.import_all(commit=True)

# Quiz.import_all(commit=True)
#QuizItem.import_all(commit=True)

#SimpleQuestionResponse.import_all(commit=True)
#CodingIoResponse.import_all(commit=True)
#QuizResponse.import_all(commit=True)

print('Converted:', OldResponse.objects.filter(is_converted=True).count(),
      'Non-converted:', OldResponse.objects.filter(is_converted=False).count())
