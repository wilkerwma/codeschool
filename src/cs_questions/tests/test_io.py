from cs_questions.tests import *
from cs_questions.tests.generic_testcases import *
question = question_io
bound_question = bound_question_io
valid_response = valid_response_io


#
# Basic binding
#
def test_question_bind_language_by_ref(question, python):
    question.bind(language=python.ref)
    assert question.language == python


def test_question_io_bind(question, user, python, source_hello_py):
    question.bind(user=user, language=python, source=source_hello_py)
    assert question.user == user
    assert question.language == python
    assert not hasattr(question, 'source')


def test_bound_question_io_response_item(bound_question, source_hello_py):
    response_item = bound_question.register_response_item(source_hello_py)
    response_item.autograde()
    assert response_item.final_grade == response_item.given_grade == 100


#
# Answer key control
#
def test_fetches_the_correct_answer_keys(question):
    key = question.answer_key_item('python')
    key.full_clean()
    assert question.iospec.is_simple_io
    assert question.iospec == key.iospec


#
# Create valid responses
#
def test_response_create_valid_feedback(question, user, source_hello_py):
    resp = question.register_response_item(user=user,
                                           source=source_hello_py,
                                           language='python')
    resp.autograde()

    # We are providing a valid source
    keys = resp.feedback_data.keys()
    assert sorted(keys) == ['answer_key', 'language', 'source', 'status',
                            'testcase']
    assert resp.feedback.testcase == resp.feedback.answer_key
    assert resp.feedback.grade == 1.0
    assert resp.feedback.status == 'ok'


def test_fetch_valid_response_from_db(valid_response):
    resp = models.CodingIoResponseItem.objects.get(id=valid_response.pk)
    assert resp.status == valid_response.status
    assert resp.final_grade == valid_response.final_grade
    assert resp.given_grade == valid_response.given_grade
    assert resp.feedback_data.keys() == valid_response.feedback_data.keys()
    assert resp.feedback.__dict__ == valid_response.feedback.__dict__


def test_access_feedback_properties(valid_response):
    resp = valid_response
    assert resp.status == 'done'
    assert resp.final_grade == 100
    assert resp.given_grade == 100
    assert resp.feedback_status == 'ok'
    assert resp.feedback_title == 'Correct Answer'
    assert resp.feedback_testcase.type == 'simple'
    assert resp.feedback_answer_key.type == 'simple'
    assert resp.feedback_hint is None
    assert resp.feedback_message is None

