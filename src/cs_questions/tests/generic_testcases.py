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
