"""
Test business logic and do not touch the database.
"""
from pytest_factoryboy import register
from codeschool.fixtures import *
from cs_questions.tests.fixtures import *
from cs_questions.models import CodingIoQuestion


@pytest.fixture
def ioquestion():
    return IoQuestionFactory.create()


@pytest.fixture
def markio_source():
    return (
"""hello
=====

    Author: """"""
    Timeout: 5.0

hello world


Description
-----------

a hello world program

Tests
-----

    who <me>
    hello me

""")


@pytest.fixture
def source_ok():
    return 'print("hello", input("who "));'


@pytest.fixture
def source_bad():
    return 'print("hello", input());'


@pytest.fixture
def source_error():
    return 'print(hello, input());'


# Markio conversion
@pytest.mark.django_db
def test_question_export(ioquestion, markio_source):
    assert ioquestion.export('markio') == markio_source


@pytest.mark.django_db
def test_question_import(ioquestion, markio_source):
    imp_question = CodingIoQuestion.from_markio(markio_source, commit=False)

    for attr in ['title', 'short_description', 'long_description', 'timeout']:
        assert getattr(ioquestion, attr) == getattr(imp_question, attr)


@pytest.mark.django_db
def test_question_import_with_empty_answer_keys(markio_source):
    ioquestion, keys = CodingIoQuestion.from_markio(markio_source,
                                                  commit=False,
                                                  return_keys=True)
    assert keys == {}


@pytest.mark.django_db
def test_question_import_with_answer_keys(markio_source):
    markio_source += (
        '\n'
        'Answer key (python)\n'
        '-------------------\n'
        '\n'
        '    print("hello", input("me "))\n'
        '\n'
    )
    ioquestion, keys = CodingIoQuestion.from_markio(markio_source,
                                                  commit=False,
                                                  return_keys=True)
    assert keys.keys() == {'python'}
    assert keys['python'].source == 'print("hello", input("me "))'
