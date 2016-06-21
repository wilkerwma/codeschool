from cs_questions.tests import *
from cs_questions.tests.generic_testcases import *
question = question_io
bound_question = bound_question_io


def test_question_bind_language_by_ref(question, python):
    question.bind(language=python.ref)
    assert question.language == python


def test_question_io_bind(question, user, python, source_hello_py):
    question.bind(user=user, language=python, source=source_hello_py)
    assert question.user == user
    assert question.language == python
    assert not hasattr(question, 'source')


def test_fetches_the_correct_answer_keys(question):
    key = question.answer_key_item('python')
    key.full_clean()
    assert question.iospec.is_simple_io
    assert question.iospec == key.iospec


def test_bound_question_io_response_item(bound_question, source_hello_py):
    response_item = bound_question.register_response_item(source_hello_py)
    response_item.autograde()
    assert response_item.final_grade == response_item.given_grade == 0


