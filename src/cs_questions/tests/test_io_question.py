import pytest
from cs_questions.tests.fixtures import *


# URL tests
@pytest.mark.django_db
def test_question_owner_urls(io_question, client):
    pk = io_question.pk
    client.force_login(io_question.owner)

    # Detail
    response = client.get('/questions/%s/' % pk)
    assert response.status_code in [200, 301]

    # Update
    response = client.get('/questions/%s/edit/' % pk)
    assert response.status_code in [200, 301]

    # Delete
    response = client.get('/questions/%s/delete/' % pk)
    assert response.status_code in [200, 301]

    # Create
    response = client.get('/questions/new/io/')
    assert response.status_code in [200, 301]


@pytest.mark.django_db
def test_user_urls(io_question, client, user):
    pk = io_question.pk
    client.force_login(user)

    # Detail
    response = client.get('/questions/%s/' % pk)
    assert response.status_code in [200, 301]

    # Update
    response = client.get('/questions/%s/edit/' % pk)
    assert response.status_code == 404

    # Delete
    response = client.get('/questions/%s/delete/' % pk)
    assert response.status_code == 404

    # Create
    response = client.get('/questions/new/io/')
    assert response.status_code == 404