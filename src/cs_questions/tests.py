import pytest
import pytest_django
from django.test import TestCase
from cs_questions import models, views


#
# Fixtures
#
@pytest.fixture(scope='session')
def io_question():
    proto = models.CodeIoQuestion(
        title='hello',
        short_description='hello world',
        long_description='a hello world program',
    )

    answer_key = models.CodeIoAnswerKey(
        source_code='print("hello world")',
        language='python',
    )

    proto.save()
    answer_key.save()
    question = models.CodeIoQuestion(
        prototype=proto,
        answer_key=answer_key,
    )
    question.save()
    return question


#
# Simple functionality
#
@pytest.mark.django_db
def test_question_exposes_prototype_attributes(io_question):
    io_proto = io_question.prototype

    for attr in ['title', 'short_description', 'long_description']:
        proto = getattr(io_proto, attr)
        question = getattr(io_question, attr)
        assert proto == question


@pytest.mark.django_db
def test_grading_io_question(io_question):
    answer = 'print("hello world")'
    response = models.Response(question=io_question, data=answer)
    feedback = io_question.grade(response)

    assert feedback.grade == 1.0
    assert not feedback.data
