from codeschool import setenv
import pytest
import pytest_django
from pytest_django.fixtures import transactional_db
from django.test import TestCase
from cs_core.models import cs_lang
from cs_questions import models, views


#
# Fixtures
#
@pytest.fixture
def io_question(db):
    question = models.CodingIoQuestion(
        title='hello',
        short_description='hello world',
        long_description='a hello world program',
        iospec='who <me>\nhello me',
    )
    question.save()
    return question


def answer_key(question, src):
    key = models.CodingIoAnswerKey(
        question=question,
        source=src,
        language=cs_lang('python')
    )
    key.save()
    return key


@pytest.fixture
def source_ok():
    return 'print("hello", input("who "));'


@pytest.fixture
def source_bad():
    return 'print("hello", input());'


@pytest.fixture
def source_error():
    return 'print(hello, input());'


@pytest.fixture
def answer_key_ok(transactional_db, question_io, source_ok):
    return answer_key(question_io, source_ok)


@pytest.fixture
def answer_key_bad(transactional_db, question_io, source_bad):
    return answer_key(question_io, source_bad)


@pytest.fixture
def answer_key_error(transactional_db, question_io, source_error):
    return answer_key(question_io, source_error)


#
# Simple functionality
#
def test_question_creates_expansion_ok(io_question, source_ok):
    Q = io_question

    Q.answer_keys.add(answer_key_ok)
    assert Q.iospec_expansions.size() == 1
    assert Q.iospec == Q.current_iospec_expansion.iospec

    exp = Q.current_iospec_expansion
    assert exp.validated_languages.size() == 1
    assert exp.invalid_languages.size() == 0

if __name__ == '__main__':
    import os
    os.chdir('../')
    os.system('')