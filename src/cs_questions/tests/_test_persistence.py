from codeschool.tests import *
from cs_questions.factories import CodingIoQuestionFactory
from cs_questions.models import CodingIoQuestion

# Fixtures
register(CodingIoQuestionFactory)


@pytest.fixture
def coding_io_question():
    return CodingIoQuestionFactory.create()


@pytest.fixture
def markio_source():
    return \
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

    who? <me>
    hello me
"""


@pytest.fixture
def full_markio_source(markio_source):
    return markio_source + \
"""

Answer Key (python)
-------------------

    print('hello', input('who? '))
"""


@pytest.fixture
def source_ok():
    return 'print("hello", input("who "));'


@pytest.fixture
def source_bad():
    return 'print("hello", input());'


@pytest.fixture
def source_error():
    return 'print(hello, input());'


# Tests ------------------------------------------------------------------------
# Markio conversion
@pytest.mark.django_db
def test_question_export(coding_io_question, full_markio_source):
    assert coding_io_question.to_markio() == full_markio_source


@pytest.mark.django_db
def test_question_import(coding_io_question, full_markio_source):
    imp_question = CodingIoQuestion.load_markio(full_markio_source)

    for attr in ['title', 'short_description', 'long_description', 'timeout']:
        assert getattr(coding_io_question, attr) == getattr(imp_question, attr)


@pytest.mark.django_db
def test_question_import_with_empty_answer_keys(markio_source):
    coding_io_question, keys = CodingIoQuestion.load_markio(markio_source,
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
    coding_io_question, keys = CodingIoQuestion.load_markio(markio_source,
                                                            commit=False,
                                                            return_keys=True)
    assert keys.keys() == {'python'}
    assert keys['python'].source == 'print("hello", input("me "))'


# URL tests --------------------------------------------------------------------
class _TestURLS(URLBaseTester):
    login_urls = [
        '/questions/',
        '/questions/{url_object.pk}/',
        '/questions/{url_object.pk}/responses',
    ]
    private_urls = [
        '/questions/{url_object.pk}/edit',
        '/questions/{url_object.pk}/delete',
    ]


