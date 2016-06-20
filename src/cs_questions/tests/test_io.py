from cs_questions.tests import *
question = question_io
bound_question = bound_question_io


# Generic question tests
def test_question_fields(question):
    assert isinstance(question.long_description, str)
    assert isinstance(question.short_description, str)


def test_question_bind_user_by_ref(question, user):
    question.bind(user=user.username)
    assert question.user == user


def test_bound_question_has_response(bound_question):
    response = bound_question.get_response()
    assert response.user == bound_question.user
    assert response.context == bound_question.context


# CodingIo specific
def test_question_bind_language_by_ref(question, python):
    question.bind(language=python.ref)
    assert question.language == python


def test_question_io_bind(question, user, python, source_py):
    question.bind(user=user, language=python, source=source_py)
    assert question.user == user
    assert question.language == python
    assert not hasattr(question, 'source')


def test_bound_question_io_response_item(bound_question, source_py):
    response_item = bound_question.register_response_item(source_py)
    response_item.autograde()
    assert response_item.final_grade == response_item.given_grade == 0


