"""
Test business logic and do not touch the database.
"""
from codeschool.fixtures import *
from cs_questions.models import CodingIoQuestion


@pytest.fixture
def use_db():
    return False


@pytest.fixture
def question(use_db):
    return saving(CodingIoQuestion(
        title='hello',
        short_description='hello world',
        long_description='a hello world program',
        iospec_source='who <me>\nhello me',
    ), use_db)


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
def test_question_export(question, markio_source):
    assert question.export('markio') == markio_source


def test_question_import(question, markio_source):
    imp_question = CodingIoQuestion.from_markio(markio_source, commit=False)

    for attr in ['title', 'short_description', 'long_description', 'timeout']:
        assert getattr(question, attr) == getattr(imp_question, attr)


def test_question_import_with_empty_answer_keys(markio_source):
    question, keys = CodingIoQuestion.from_markio(markio_source,
                                                  commit=False,
                                                  return_keys=True)
    assert keys == {}


def test_question_import_with_answer_keys(markio_source):
    markio_source += (
        '\n'
        'Answer key (python)\n'
        '-------------------\n'
        '\n'
        '    print("hello", input("me "))\n'
        '\n'
    )
    question, keys = CodingIoQuestion.from_markio(markio_source,
                                                  commit=False,
                                                  return_keys=True)
    assert keys.keys() == {'python'}
    assert keys['python'].source == 'print("hello", input("me "))'